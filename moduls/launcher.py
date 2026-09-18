import asyncio
import subprocess, requests
from pathlib import Path
from infrastructure_process_utils import find_free_port, PidManager
from infrastructure_http_clients import ServerProbe
from infrastructure_path_utils import get_root_dir_path
from typing import Any, Literal


class Launcher:
    def __init__(self, target_dir: Path):
        self._running = False
        self._target_dir = target_dir
        self.run_services: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._pid_manager = PidManager(pid_file_path=get_root_dir_path() / 'pids.txt')

    async def start(
            self, services: dict[str, dict[str, Any]],
            timeout_run_server: float = 180.0,
            log_level: Literal['debug', 'info', 'warning', 'error'] = 'info',
    ):
        self._running = True
        self._pid_manager.stop()  # остановить предыдущие pid (если программа завершилась не корректно)
        tasks = []
        for svc in services:
            svc_path = self._target_dir / svc / 'app.exe'
            if not svc_path.exists():
                continue

            # запуск сервера
            task = asyncio.create_task(
                self._run_server(
                    svc_path=svc_path,
                    svc_name=svc,
                    timeout_run_server=timeout_run_server,
                    log_level=log_level,
                    svc_parameters=services[svc],
                )
            )
            tasks.append(task)

        # ожидание запуска всех серверов
        await asyncio.gather(*tasks, return_exceptions=False)

    async def stop(self, timeout_stop_server: float = 180.0):
        tasks = []
        for svc_name, port in self.run_services.items():
            task = asyncio.create_task(
                self._stop_server(
                    svc_name=svc_name,
                    port=port,
                    timeout_stop_server=timeout_stop_server
                )
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)  # дождаться остановки серверов
        self._pid_manager.clear()  # всё завершилось корректно, очистить pid менеджер
        self._running = False

    async def _run_server(
            self, svc_path: Path, svc_name: str, svc_parameters: dict[str, Any],
            log_level: Literal['debug', 'info', 'warning', 'error'] = 'info',
            timeout_run_server: float = 180.0,
    ):
        port = find_free_port(start_port=8000, max_attempts=100, ignore_ports_list=list(self.run_services.values()))
        async with self._lock:
            self.run_services[svc_name] = port
        cmd = [svc_path, 'run-server', '--port', str(port), '--log-level', log_level]
        process = await asyncio.to_thread(lambda: subprocess.Popen(cmd))

        # проверка что сервер был запущен
        try:
            res: requests.Response = await asyncio.to_thread(
                lambda: ServerProbe.wait_for_server_up(
                    url=f'http://localhost:{port}/health/',
                    timeout=timeout_run_server,
                    expected_status=200,
                )
            )
            if res.status_code != 200:
                raise RuntimeError(f'Сервер {svc_name} не был запущен')
        except Exception as err:
            raise RuntimeError(f'Не удалось запустить сервер `{svc_name}`, ошибка: {err}')

        # получение pid сервера
        res = await asyncio.to_thread(lambda: requests.get(f'http://localhost:{port}/pid/'))
        if res.status_code != 200:
            raise RuntimeError(f'Сервер `{svc_name}` не выдает pid')
        res = res.json()
        pid = res.get('pid', None)  # noqa
        if pid is None:
            raise RuntimeError(f'Не получен pid для сервера {svc_name}')
        self._pid_manager.add(pid)

        # запуск сервера с параметрами
        res = await asyncio.to_thread(
            lambda: requests.post(url=f'http://localhost:{port}/start/', json=svc_parameters))
        if res.status_code != 200:
            raise RuntimeError(f'Engine сервера `{svc_name}` не был запущен')
        return process

    @staticmethod
    async def _stop_server(svc_name, port, timeout_stop_server: float = 180.0):
        await asyncio.to_thread(lambda: requests.get(f'http://localhost:{port}/stop/'))  # остановить engine сервера
        await asyncio.to_thread(lambda: requests.get(f'http://localhost:{port}/shutdown/'))  # остановить сервер
        # проверка что сервер был остановлен
        try:
            await asyncio.to_thread(
                lambda: ServerProbe.wait_for_server_down(
                    url=f'http://localhost:{port}/health/',
                    timeout=timeout_stop_server,
                )
            )
        except Exception as err:
            raise RuntimeError(f'Не удалось запустить сервер `{svc_name}`, ошибка: {err}')


async def main():
    launcher = Launcher(target_dir=Path(r'C:\Users\projects\Desktop\demo'))
    await launcher.start(
        services={
            'srv_stt_vosk': {
                'samplerate': 16000,
                'blocksize': 1024,
                'model': 'vosk-model-small-ru-0.22'
            },
        }
    )
    await asyncio.to_thread(lambda: input('...'))  # временно имитация задержки
    await launcher.stop()


if __name__ == '__main__':
    asyncio.run(main())
