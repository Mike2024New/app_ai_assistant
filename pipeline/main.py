import asyncio
from clients import STTClient
from clients import TTSClient
from clients import LLMClient
from datetime import datetime
from string import ascii_lowercase

"""
Реализация полезной нагрузки приложения (пайплайн).
"""


class Pipeline:
    def __init__(self, services: dict[str, int], queue_dialog: asyncio.Queue):
        self._stt = STTClient(port=services['srv_stt'])
        self._tts = TTSClient(port=services['srv_tts'])
        self._llm = LLMClient(port=services['srv_llm'])
        self._event = asyncio.Event()
        self._event_new_speech = asyncio.Event()
        self._event_interrupt = asyncio.Event()
        self._queue_dialog = queue_dialog
        self._ai_text = ''

    async def interrupt_observer(self):
        """Начали говорить? Сразу прервать и генерацию токенов и tts"""
        while not self._event.is_set():
            await asyncio.sleep(0.01)
            if self._event_interrupt.is_set():
                if self._ai_text:
                    now = datetime.now().strftime('%d.%m.%Y %H:%M:%S.%f')  # noqa
                    self._queue_dialog.put_nowait(f' [ {now} ] ai: {self._ai_text.strip()}')  # noqa
                    self._ai_text = ''

                self._llm.interrupt()
                await self._tts.interrupt()
                self._event_interrupt.clear()

    async def start(self):
        asyncio.create_task(self.interrupt_observer())
        asyncio.create_task(
            self._stt.listen(
                event=self._event,
                callback=self._callback,
                event_interrupt=self._event_interrupt
            )
        )

    async def stop(self):
        self._event.set()

    async def _tts_callback(self, sentence):
        self._ai_text += sentence

        def is_russian(text: str) -> bool:
            """Выбор спикера в зависимости от того каких слов больше"""
            ru_chars = list('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
            counter = {'ru': 0, 'en': 0}
            for ch in text:
                if ch in ru_chars:
                    counter['ru'] += 1
                if ch in ascii_lowercase:
                    counter['en'] += 1
            return counter['ru'] > counter['en'] or not counter['en']

        # fallback на английский, если приложение на английском языке
        speaker = 'aidar' if is_russian(sentence) else 'en_101'
        await self._tts.say(text=sentence, speaker=speaker, add=True)

    async def _callback(self, text):
        now = datetime.now().strftime('%d.%m.%Y %H:%M:%S.%f')
        self._queue_dialog.put_nowait(f' [ {now} ] user: {text.strip()}')
        asyncio.create_task(self._llm.ask_and_sentence(prompt=text, callback=self._tts_callback))

# пример запуска пайплайна (сервисы srv_llm, srv_stt, srv_tts должны быть запущены а их порты известны)
# async def main():
#     pipeline = Pipeline(
#         services={
#             'srv_llm': 8000,
#             'srv_stt': 8001,
#             'srv_tts': 8002,
#         }
#     )
#     await pipeline.start()
#     await asyncio.to_thread(lambda: input('...press enter for exit...\n'))
#     await pipeline.stop()
#
#
# if __name__ == '__main__':
#     asyncio.run(main())
