import asyncio, requests, websockets, json


class STTClient:
    def __init__(self, port: int):
        self._port = port
        self._check_state_server()

    def _check_state_server(self):
        """Проверка что сервер запущен"""
        res = requests.get(url=f'http://localhost:{self._port}/parameters/')
        if not res.json().get('running', None):
            raise RuntimeError(f'движок сервера не запущен')

    async def listen(self, event: asyncio.Event, callback):
        async with websockets.connect(f'ws://127.0.0.1:{self._port}/ws') as ws:
            try:
                async def consumer():
                    while not event.is_set():
                        try:
                            # во избежание зависания стриминга желательно использовать wait_for
                            data = await asyncio.wait_for(ws.recv(), timeout=0.1)
                            data = json.loads(data)  # пример: {'type': 'result', 'text': 'распознанный текст'}
                            text = data.get('text', '')
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

    async def callback(res):
        print(res)

    asyncio.create_task(stt.listen(event=event, callback=callback))
    await asyncio.to_thread(lambda: input('...press enter for exit...\n'))
    event.set()


if __name__ == '__main__':
    asyncio.run(main())
