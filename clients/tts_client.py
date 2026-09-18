import asyncio, requests


class TTSClient:
    def __init__(self, port: int):
        self._port = port
        self._check_state_server()
        self.speakers = []
        self._get_speakers()

    def _check_state_server(self):
        """Проверка что сервер запущен"""
        res = requests.get(url=f'http://localhost:{self._port}/parameters/')
        if not res.json().get('running', None):
            raise RuntimeError(f'движок сервера не запущен')

    def _get_speakers(self):
        """Получить голоса доступные для моделей"""
        res = requests.get(url=f'http://localhost:{self._port}/models/')
        if res.status_code != 200:
            raise RuntimeError(f'Сервер не отдает список спикеров.')
        speakers = res.json()
        for key in speakers:
            self.speakers.extend(speakers[key])

    async def say(self, text: str, speaker: str, add: bool = True) -> None:
        """
        Произнести текст в аудио
        :param text: фраза которую нужно произнести
        :param speaker: голос модели (см доступные в speakers)
        :param add: True - добавить текст, к произносящемуся, False - прервать произносящийся текст и начать новый
        :return: None
        """
        if speaker not in self.speakers:
            raise RuntimeError(f'speaker {speaker} не существует, выберите из {self.speakers}')
        await asyncio.to_thread(
            lambda: requests.post(
                url=f'http://localhost:{self._port}/execute/',
                json={'text': text, 'speaker': speaker, 'add': add}
            )
        )

    async def interrupt(self):
        """Прерывать речь, но обычно достаточно say, с флагом add=False"""
        await asyncio.to_thread(lambda: requests.get(url=f'http://localhost:{self._port}/interrupt/'))


async def main():
    tts = TTSClient(port=8002)
    print(tts.speakers)
    # await tts.say(text='Привет, расскажи о первых компьютерах?', speaker='xenia', add=True)
    # await tts.say(text='Привет, ну первые компьютеры появились не в пещерах.', speaker='aidar', add=True)
    # await asyncio.sleep(4)
    # await tts.say(text='Хватит, душнить! Расскажи кратко.', speaker='xenia', add=False)
    # await asyncio.sleep(2)


if __name__ == '__main__':
    asyncio.run(main())
