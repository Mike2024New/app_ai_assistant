import asyncio, requests, websockets, json
from typing import Callable, Awaitable

POLL_INTERVAL = 0.006  # частота asyncio.sleep (высвобождение потока для внешнего цикла событий)


class STTClient:
    def __init__(self, port: int, event: asyncio.Event):
        self._port = port
        self._check_state_server()
        self._new_speech = False
        self._event = event
        self._event_interrupt = asyncio.Event()

    async def observer(self, callback: Callable[[], Awaitable[None]]):
        """
        Начали говорить (пришел первый partial)? Немедленно выполнить callback
        """
        while not self._event.is_set():
            await asyncio.sleep(POLL_INTERVAL)
            if self._event_interrupt.is_set():
                await callback()
                self._event_interrupt.clear()

    def _check_state_server(self):
        """Проверка что сервер запущен"""
        res = requests.get(url=f'http://localhost:{self._port}/parameters/')
        if not res.json().get('running', None):
            raise RuntimeError(f'движок сервера не запущен')

    async def listen(self, callback: Callable[[str], Awaitable[None]]):
        async with websockets.connect(f'ws://127.0.0.1:{self._port}/ws') as ws:
            try:
                async def consumer():
                    select_engine = 'vosk'
                    # просто бесконечный цикл, принимающий чанки с сокета
                    while not self._event.is_set():
                        try:
                            data = await asyncio.wait_for(ws.recv(), timeout=0.1)
                            data = json.loads(data)  # пример: {'type': 'result', 'text': 'распознанный текст'}

                            if data.get('type', None) == 'metadata':
                                # через метадата видно какой движок был выбран в /start/
                                select_engine = 'whisper' if 'whisper' in data.get('engines', []) else select_engine
                            elif data.get('type', None) == 'partial':
                                if not self._new_speech:
                                    self._new_speech = True
                                    self._event_interrupt.set()  # начали новую речь, прервать всех ассистентов
                            elif data.get('type', None) == 'result' and data.get('engine', None) == select_engine:
                                text = data.get('text', '')
                                self._new_speech = False
                                await callback(text)
                        except asyncio.TimeoutError:
                            pass

                task = asyncio.create_task(consumer())
                await task

            except websockets.exceptions.ConnectionClosedOK:
                # соединение закрыто штатно, всё в порядке
                pass

            except Exception as err:  # обработка ошибки, логировать -> пробросить
                print(f'Ошибка соединения {err}')
                raise


async def main():
    # для работы этого примера нужен запущенный сервер
    event = asyncio.Event()
    stt = STTClient(port=8001, event=event)

    async def listen_callback(res):
        print(res)

    async def observer_callback():
        print(f'Начали говорить')

    asyncio.create_task(stt.listen(callback=listen_callback))
    asyncio.create_task(stt.observer(callback=observer_callback))
    await asyncio.to_thread(lambda: input('...press enter for exit...\n'))
    event.set()


if __name__ == '__main__':
    asyncio.run(main())
