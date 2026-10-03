import asyncio, requests, websockets, json


class STTClient:
    def __init__(self, port: int):
        self._port = port
        self._check_state_server()
        self._new_speech = False

    def _check_state_server(self):
        """Проверка что сервер запущен"""
        res = requests.get(url=f'http://localhost:{self._port}/parameters/')
        if not res.json().get('running', None):
            raise RuntimeError(f'движок сервера не запущен')

    async def listen(self, event: asyncio.Event, callback, event_interrupt: asyncio.Event):
        async with websockets.connect(f'ws://127.0.0.1:{self._port}/ws') as ws:
            try:
                async def consumer():
                    select_engine = 'vosk'
                    while not event.is_set():
                        try:
                            data = await asyncio.wait_for(ws.recv(), timeout=0.1)
                            data = json.loads(data)  # пример: {'type': 'result', 'text': 'распознанный текст'}

                            if data.get('type', None) == 'metadata':
                                select_engine = 'whisper' if 'whisper' in data.get('engines', []) else select_engine
                            elif data.get('type', None) == 'partial':
                                if not self._new_speech:
                                    self._new_speech = True
                                    event_interrupt.set()  # начали новую речь, прервать всех ассистентов
                            elif data.get('type', None) == 'result' and data.get('engine', None) == select_engine:
                                text = data.get('text', '')
                                self._new_speech = False
                                # print(text)
                                await callback(text)
                        except asyncio.TimeoutError:
                            pass

                task = asyncio.create_task(consumer())
                await task

            except websockets.exceptions.ConnectionClosedOK:
                event.set()  # соединение закрыто штатно, всё в порядке, не логировать

            except Exception as err:  # обработка ошибки, логировать
                print(f'Ошибка соединения {err}')
                event.set()


async def main():
    stt = STTClient(port=8000)
    event = asyncio.Event()
    event_interrupt = asyncio.Event()

    async def callback(res):
        print(res)

    async def observer():
        while True:
            await asyncio.sleep(0.05)
            if event_interrupt.is_set():
                print('новая речь')
                event_interrupt.clear()

    asyncio.create_task(observer())
    asyncio.create_task(stt.listen(event=event, callback=callback, event_interrupt=event_interrupt))
    await asyncio.to_thread(lambda: input('...press enter for exit...\n'))
    event.set()


if __name__ == '__main__':
    asyncio.run(main())
