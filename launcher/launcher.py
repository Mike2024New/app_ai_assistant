import asyncio
import subprocess, requests
from pathlib import Path
from infrastructure_process_utils import find_free_port, PidManager
from infrastructure_http_clients import ServerProbe
from infrastructure_path_utils import get_root_dir_path, find_interpreter_by_root_dir
from typing import Any, Literal
from config import time_utils, settings, EXE_MODE

CREATE_NO_WINDOW = 0x08000000  # флаг Windows для скрытия консоли (которая появлялась на win11)

"""
Лаунчер для запуска сервисов прописанных в settings.json
Его задача, просто запустить сервисы передав в них стартовые параметры ( /start/ ). 
И остановить все компоненты по команде ( /stop/ /shutdown/ )
"""


class Launcher:
    def __init__(self, queue_launcher: asyncio.Queue, target_dir: Path | None = None):
        self._running = False
        self._queue_launcher = queue_launcher
        # если корневая директория сервисов не передана явно, то по умолчанию поиск на папку на уровень выше
        self._root_dir = target_dir if target_dir else get_root_dir_path().parent
        self.run_services: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._pid_manager = PidManager(pid_file_path=get_root_dir_path() / 'pids.txt')

    async def start(
            self, timeout_run_server: float = 180.0,
            log_level: Literal['debug', 'info', 'warning', 'error'] = 'info',
    ):
        self._running = True
        self._pid_manager.stop()  # остановить предыдущие pid (если программа завершилась не корректно)
        tasks = []
        services = settings.services
        for svc in services:
            svc_path = self._root_dir / svc if EXE_MODE else self._root_dir / svc
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

        # уведомить приложение о запуске
        self._queue_launcher.put_nowait(
            {
                'timestamp': time_utils.timestamp(),
                'msg': f'Запуск компонента {svc_name}',
                'type': 'start',
            }
        )

        port = find_free_port(start_port=8000, max_attempts=100, ignore_ports_list=list(self.run_services.values()))
        async with self._lock:
            self.run_services[svc_name] = port

        if EXE_MODE:
            # запуск в режиме обычного приложения
            cmd = [svc_path / 'app.exe', 'run-server', '--port', str(port), '--log-level', log_level]
        else:
            # запуск из кода (для разработки)
            interpreter_path = find_interpreter_by_root_dir(svc_path)
            if interpreter_path is None:
                raise RuntimeError(f'Не найден интерпретатор сервиса `{svc_name}`')
            cmd = [interpreter_path, 'cli.py', 'run-server', '--port', str(port), '--log-level', log_level]

        process = await asyncio.to_thread(
            lambda: subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW,
                cwd=svc_path,
            )
        )

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
            self._queue_launcher.put_nowait({
                'timestamp': None, 'msg': f'Не удалось запустить сервер `{svc_name}`, ошибка: {err}',
                'type': 'error',
            })
            self._queue_launcher.put_nowait(None)
            raise RuntimeError(f'Не удалось запустить сервер `{svc_name}`, ошибка: {err}')

        # получение pid сервера
        res = await asyncio.to_thread(lambda: requests.get(f'http://localhost:{port}/pid/'))
        if res.status_code != 200:
            self._queue_launcher.put_nowait({
                'timestamp': None, 'msg': f'Сервер `{svc_name}` не выдает pid',
                'type': 'error',
            })
            self._queue_launcher.put_nowait(None)
            raise RuntimeError(f'Сервер `{svc_name}` не выдает pid')
        res = res.json()
        pid = res.get('pid', None)  # noqa
        if pid is None:
            self._queue_launcher.put_nowait({
                'timestamp': None, 'msg': f'Не получен pid для сервера {svc_name}',
                'type': 'error',
            })
            self._queue_launcher.put_nowait(None)
            raise RuntimeError(f'Не получен pid для сервера {svc_name}')
        self._pid_manager.add(pid)

        # запуск сервера с параметрами
        res = await asyncio.to_thread(
            lambda: requests.post(url=f'http://localhost:{port}/start/', json=svc_parameters))
        if res.status_code != 200:
            self._queue_launcher.put_nowait({
                'timestamp': time_utils.timestamp(),
                'msg': f'Engine компонента {svc_name} не был запущен',
                'type': 'error',
            })
            self._queue_launcher.put_nowait(None)
            raise RuntimeError(f'Engine сервера `{svc_name}` не был запущен')

        # уведомить приложение о запуске
        self._queue_launcher.put_nowait({
            'timestamp': time_utils.timestamp(),
            'msg': f'Компонент {svc_name} запущен. Порт {port}, pid {pid}, url {f"http://localhost:{port}/docs/"}',
            'type': 'start',
        })
        return process

    async def _stop_server(self, svc_name, port, timeout_stop_server: float = 180.0):
        self._queue_launcher.put_nowait({
            'timestamp': time_utils.timestamp(),
            'msg': f'Остановка компонента {svc_name}.',
            'type': 'stop',
        })
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

        self._queue_launcher.put_nowait(
            {
                'timestamp': time_utils.timestamp(),
                'msg': f'Компонент {svc_name} остановлен.',
                'type': 'stop',
            }
        )


if __name__ == '__main__':
    async def launcher_observer(queue_launch: asyncio.Queue):
        """Наблюдение за лаунчером (возвращает в очередь результаты)"""
        while True:
            try:
                res = await  asyncio.wait_for(queue_launch.get(), timeout=0.4)
                if res is None:
                    break
                print(res)
            except asyncio.TimeoutError:
                pass


    async def example():
        queue_launcher = asyncio.Queue()
        launcher = Launcher(queue_launcher=queue_launcher)
        asyncio.create_task(launcher_observer(queue_launch=queue_launcher))
        await launcher.start()
        await asyncio.to_thread(lambda: input('...'))
        await launcher.stop()


    asyncio.run(example())
