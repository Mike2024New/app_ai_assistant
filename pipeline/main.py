import asyncio
from string import ascii_lowercase
from config import settings, time_utils
from clients import STTClient
from clients import TTSClient
from clients import LLMClient

"""
Реализация полезной нагрузки приложения (пайплайн).
"""


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


class Pipeline:
    def __init__(self):
        self._running = False
        self._stt: STTClient | None = None
        self._tts: TTSClient | None = None
        self._llm: LLMClient | None = None
        self._event = asyncio.Event()
        self.queue = asyncio.Queue()
        self._stt_observer_task: asyncio.Task | None = None
        self._stt_callback_task: asyncio.Task | None = None
        self._llm_task: asyncio.Task | None = None

    async def observer_callback(self):
        self._llm.interrupt()
        if self._llm_task is not None and not self._llm_task.done():
            self._llm_task.cancel()
            await asyncio.gather(self._llm_task, return_exceptions=True)  # придавить задачу
        await self._tts.interrupt()

    async def start(self, services: dict[str, int]):
        if self._running:
            return
        self._running = True
        self._stt: STTClient | None = STTClient(port=services['srv_stt'], event=self._event)
        self._tts: TTSClient | None = TTSClient(port=services['srv_tts'])
        self._llm: LLMClient | None = LLMClient(port=services['srv_llm'], event=self._event)
        # запуск stt с callback функциями
        # действия в случае если новая речь
        self._stt_observer_task = asyncio.create_task(self._stt.observer(callback=self.observer_callback))
        # действия с услышанными фразами
        self._stt_callback_task = asyncio.create_task(self._stt.listen(callback=self._stt_callback))

    async def stop(self):
        if not self._running:
            return
        self.queue.put_nowait(None)  # sentinel
        self._event.set()  # прервать все дочерние процессы (stt, llm, tts)
        await self.observer_callback()  # появилась новая речь остановить llm и tts
        # дождаться завершения всех задач
        self._running = False

    async def _tts_callback(self, sentence):
        # fallback на английский, если приложение на английском языке
        speaker = settings.speakers["ru"] if is_russian(sentence) else settings.speakers["en"]
        self.queue.put_nowait({
            'role': 'ai', 'text': sentence.strip(), 'timestamp': time_utils.timestamp(), 'type': 'process',
        })
        await self._tts.say(text=sentence, speaker=speaker, add=True)

    async def _stt_callback(self, text):
        # реакция на полученную фразу
        self.queue.put_nowait({
            'role': 'user', 'text': text.strip(), 'timestamp': time_utils.timestamp(), 'type': 'process',
        })
        # отправить полученную от пользователя фразу в ИИ
        self._llm_task = asyncio.create_task(self._llm.ask_and_sentence(prompt=text, callback=self._tts_callback))

    async def observer(self, callback):
        """Обсервер, наблюдает за очередью (для ui и консольных интерфейсов), запускается отдельно через create_task"""
        while True:
            try:
                res = await asyncio.wait_for(self.queue.get(), 0.5)
                if res is None:
                    break
                if callback is not None:
                    callback(res)
            except asyncio.TimeoutError:
                pass
