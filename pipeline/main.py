import asyncio
from string import ascii_lowercase
from config import settings, time_utils
from clients import STTClient
from clients import TTSClient
from clients import LLMClient

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
            await asyncio.sleep(0.01)  # отдать поток управления внешнему циклу событий

            # текст прервали, отдать то что успел сгенерить ИИ в очередь и прервать процессы генерации
            if self._event_interrupt.is_set():
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
        self._queue_dialog.put_nowait(None)  # sentinel
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
        speaker = settings.speakers["ru"] if is_russian(sentence) else settings.speakers["en"]
        self._queue_dialog.put_nowait({
            'role': 'ai', 'text': sentence.strip(), 'timestamp': time_utils.timestamp(), 'type': 'process',
        })
        await self._tts.say(text=sentence, speaker=speaker, add=True)

    async def _callback(self, text):
        self._queue_dialog.put_nowait({
            'role': 'user', 'text': text.strip(), 'timestamp': time_utils.timestamp(), 'type': 'process',
        })
        # отправить полученную от пользователя фразу в ИИ
        asyncio.create_task(self._llm.ask_and_sentence(prompt=text, callback=self._tts_callback))
