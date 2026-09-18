import asyncio, requests, websockets, json


class LLMClient:
    def __init__(self, port: int):
        self._port = port
        self._check_state_server()
        self.event = asyncio.Event()

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

                while not self.event.is_set():
                    data = await ws.recv()
                    data = json.loads(data)
                    # модель пометит последний токен как end например: {'token': 'null', 'type': 'end'}
                    if data.get('type', None) == 'end':
                        await callback(None)
                        break
                    # в этой точке можно обработать токены, например собрать их в приложение и отправить в tts для озвучки
                    token = data.get('token', '')  # пример {'token': 'фрагмент', 'type': 'mid'}
                    await callback(token)

            except websockets.exceptions.ConnectionClosedOK:
                self.event.set()  # соединение закрыто штатно, всё в порядке, не логировать

            except Exception as err:  # обработка ошибки, логировать
                print(f'Ошибка соединения {err}')
                self.event.set()

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
    llm_client = LLMClient(port=8000)

    async def callback(sentence):
        print(sentence)

    await llm_client.ask_and_sentence(prompt='Привет, как дела? У меня не много времени, но я рад общению.',
                                      callback=callback)
    await asyncio.to_thread(lambda: input('...press enter for exit...\n'))


if __name__ == '__main__':
    asyncio.run(main())
