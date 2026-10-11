import asyncio, requests, websockets, json

WAIT_FOR_TIMEOUT = 0.5


class LLMClient:
    def __init__(self, port: int, event: asyncio.Event):
        self._port = port
        self._check_state_server()
        self._event = event
        self._inner_event = asyncio.Event()

    def interrupt(self):
        """Прерывание генерации токенов моделью на лету"""
        self._inner_event.set()

    def _check_state_server(self):
        """Проверка что сервер запущен"""
        res = requests.get(url=f'http://localhost:{self._port}/parameters/')
        if not res.json().get('running', None):
            raise RuntimeError(f'движок сервера не запущен')

    async def ask(self, prompt: str, callback):
        async with websockets.connect(f'ws://localhost:{self._port}/ws') as ws:
            """Пример использования, отправка промпта и получение готовых токенов"""
            try:
                prompt = json.dumps({'prompt': prompt})
                await ws.send(prompt)  # отправка промпта
                self._inner_event.clear()
                while not self._inner_event.is_set():
                    if self._event.is_set():  # общий выход
                        break
                    try:
                        data = await asyncio.wait_for(ws.recv(), timeout=WAIT_FOR_TIMEOUT)
                        data = json.loads(data)
                        # модель пометит последний токен как end например: {'token': 'null', 'type': 'end'}
                        if data.get('type', None) == 'end':
                            await callback(None)
                            break
                        # в этой точке можно обработать токены, например собрать их в приложение и отправить в tts для озвучки
                        token = data.get('token', '')  # пример {'token': 'фрагмент', 'type': 'mid'}
                        await callback(token)  # ответы от llm
                    except asyncio.TimeoutError:
                        pass

            except websockets.exceptions.ConnectionClosedOK:
                self._inner_event.set()  # соединение закрыто штатно, всё в порядке, не логировать

            except Exception as err:  # обработка ошибки, логировать
                print(f'Ошибка соединения {err}')
                self._inner_event.set()

    async def ask_and_sentence(self, prompt: str, callback):
        sentence = ''

        async def token_receive_callback(token):
            nonlocal sentence

            if token is None:
                return

            if any(char in '.!?,' for char in token):
                sentence += token
                await callback(sentence)  # действие с предложением
                sentence = ''  # обнуление предложения
                return

            sentence += token if token is not None else ''

        await self.ask(prompt=prompt, callback=token_receive_callback)


async def main():
    # для этого примера требуется запущенный сервис srv_llm
    event = asyncio.Event()  # общий остановщик
    llm_client = LLMClient(port=8000, event=event)

    async def callback(sentence):
        """Сюда складываются предложения от llm"""
        print(sentence, end=' ')

    # ожидание ответа от llm
    asyncio.create_task(
        llm_client.ask_and_sentence(
            prompt='Привет, расскажи о себе как можно более подробно.',
            callback=callback
        )
    )
    await asyncio.sleep(2)  # llm начинает отвечать и прерывается
    # await asyncio.to_thread(lambda: input('...press enter for exit...\n')) # для проверки мгновенного прерывания
    event.set()  # остановка llm клиента (подстраховка, если запуск через create_task без await то не обязательно)
    await asyncio.sleep(20)


if __name__ == '__main__':
    asyncio.run(main())
