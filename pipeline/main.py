import asyncio, json
from string import ascii_lowercase
from config import settings, time_utils, history_messages_json, commands
from clients import STTClient
from clients import TTSClient
from clients import LLMClient
from pipeline.comand_executor import executor

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
        self._llm_first_message: bool = False  # проверка, что llm успел ответить хоть что-то (исключ пустых запусков)
        self._event = asyncio.Event()
        self.queue = asyncio.Queue()
        self._stt_observer_task: asyncio.Task | None = None
        self._stt_callback_task: asyncio.Task | None = None
        self._llm_task: asyncio.Task | None = None
        self._stop_assistant_wait: bool = False

    async def observer_callback(self):
        self._llm.interrupt()
        if self._llm_task is not None and not self._llm_task.done():
            # проверить это место, ибо во время резюме зависает !!!
            self._llm_task.cancel()
            await asyncio.gather(self._llm_task, return_exceptions=True)  # придавить задачу
        await self._tts.interrupt()

    async def start(self, services: dict[str, dict[str, int]]):
        if self._running:
            return
        self._running = True
        self._stt = STTClient(port=services['srv_stt']['port'], event=self._event)
        self._tts = TTSClient(port=services['srv_tts']['port'])
        self._llm = LLMClient(port=services['srv_llm']['port'], event=self._event)

        # загрузка истории сообщений (продолжение диалога с llm - примитивная долговременная память)
        if not settings.services['srv_llm']['one_message_mode'] and history_messages_json.exists():
            self.queue.put_nowait({
                'role': 'user', 'text': 'загрузка истории сообщений', 'timestamp': time_utils.timestamp(),
                'type': 'process',
            })
            try:
                with open(file=history_messages_json, mode='r', encoding='utf-8') as f:
                    data = json.loads(f.read())
                await self._llm.set_history_messages(history_messages=data)
            except Exception as err:
                print(err)
                self.queue.put_nowait({
                    'role': 'user', 'text': 'не удалось загрузить историю сообщений',
                    'timestamp': time_utils.timestamp(),
                    'type': 'process',
                })

        # запуск stt с callback функциями
        # действия в случае если новая речь
        self._stt_observer_task = asyncio.create_task(self._stt.observer(callback=self.observer_callback))
        # действия с услышанными фразами
        self._stt_callback_task = asyncio.create_task(self._stt.listen(callback=self._stt_callback))

    async def stop(self):
        self._stop_assistant_wait = True
        if not self._running:
            return

        # загрузка истории сообщений (продолжение диалога с llm - примитивная долговременная память)
        if not settings.services['srv_llm']['one_message_mode'] and self._llm_first_message:
            self.queue.put_nowait({
                'role': 'user', 'text': 'сжатие истории сообщений', 'timestamp': time_utils.timestamp(),
                'type': 'process',
            })
            summary = await self._llm.get_history_messages()  # llm проводит суммаризацию
            with open(file=history_messages_json, mode='w', encoding='utf-8') as f:
                summary = {'history_messages': summary}
                f.write(json.dumps(summary, ensure_ascii=False, indent=2))

        self.queue.put_nowait(None)  # sentinel
        self._event.set()  # прервать все дочерние процессы (stt, llm, tts)
        await self.observer_callback()  # появилась новая речь остановить llm и tts
        self._running = False

    async def _tts_callback(self, sentence):
        # fallback на английский, если приложение на английском языке
        speaker = settings.speakers["ru"] if is_russian(sentence) else settings.speakers["en"]
        self.queue.put_nowait({
            'role': 'ai', 'text': sentence.strip(), 'timestamp': time_utils.timestamp(), 'type': 'process',
        })
        await self._tts.say(text=sentence, speaker=speaker, add=True)
        self._llm_first_message = True

    async def _stt_callback(self, text):
        if self._stop_assistant_wait:
            # идет суммаризация после выключения ассистента -> игнорировать вхождения на микрофон
            return

        # отлов команд, здесь именно можно ловить ассистентов и передавать точечный запрос в llm
        if settings.assistant:
            for i in (settings.assistant_name,):
                first_word = text.split()[0].lower().strip('.,!?;:') if text else ''
                if first_word.lower() == i.lower():
                    command = ' '.join(text.split()[1:]).strip().lower()

                    self.queue.put_nowait({
                        'role': 'user', 'text': f'cmd: {text}'.strip(), 'timestamp': time_utils.timestamp(),
                        'type': 'process',
                    })

                    # сперва грубый эвристичный поиск
                    if command in commands:
                        try:
                            res = executor(command)
                            if res:
                                await self._tts.say(
                                    text=res,
                                    speaker=settings.speakers["ru"],
                                    add=True
                                )
                        except Exception:  # noqa
                            await self._tts.say(
                                text='ошибка во время выполнения команды',
                                speaker=settings.speakers["ru"],
                                add=True
                            )

                    else:
                        # в этой точке можно отправить сырой запрос llm без истории в one message, чтобы он помог определить
                        await self._tts.say(text='Не распознанная команда', speaker=settings.speakers["ru"], add=True)
                    return

        self.queue.put_nowait({
            'role': 'user', 'text': text.strip(), 'timestamp': time_utils.timestamp(), 'type': 'process',
        })
        if settings.companion:
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
