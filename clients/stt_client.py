import asyncio, requests, websockets, json
from time import perf_counter
from typing import Callable, Awaitable
from config import logger, settings

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
                    whisper_timeout_sec = settings.whisper_timeout_sec  # сколько ждать whisper?
                    priority_words = (settings.assistant_name,)  # ключевые слова в начале (vosk быстрее распознает их)

                    # Состояние текущей фразы
                    current_request_id = None  # контекст для ожидания whisper
                    current_answers = []  # накопитель результатов
                    vosk_received_at = None  # время получения ответа от Vosk

                    def reset_state():
                        """Сброс состояния после обработки фразы."""
                        nonlocal current_request_id, current_answers, vosk_received_at
                        current_request_id = None
                        current_answers = []
                        vosk_received_at = None

                    async def process_final_answers(answers: list):
                        """Единая точка отправки ответа в пайплайн (LLM/TTS)."""
                        self._new_speech = False

                        # фильтр для чисел - whisper распознает числа но формат не всегда точный, vosk пишет их словами, для llm это лучше
                        if settings.stt_numbers_filter and len(answers) > 1:
                            for row in answers:
                                sentence = row['text']
                                if any(char.isdigit() for char in sentence):
                                    answers = [answers[0]]
                                    break

                        # отдать в callback актуальный ответ, если отработал только vosk значит его, если whisper то он приоритетнее
                        await callback(answers[-1].get('text'))

                    def is_priority_command(text_in: str) -> bool:
                        """Проверяет, начинается ли фраза с кодового слова."""
                        for i in priority_words:
                            first_word = text_in.split()[0].lower().strip('.,!?;:') if text_in else ''
                            if first_word.lower() == i.lower():
                                return True
                        return False

                    # просто бесконечный цикл, принимающий чанки с сокета
                    while not self._event.is_set():
                        try:
                            data = await asyncio.wait_for(ws.recv(), timeout=0.1)
                            data = json.loads(data)  # пример: {'type': 'result', 'text': 'распознанный текст'}

                            msg_type = data.get('type')

                            if msg_type == 'metadata':
                                if 'whisper' not in data.get('engines') and whisper_timeout_sec != 0:
                                    # whisper отсутствует в движках, ждать нет смысла, занулить таймаут
                                    whisper_timeout_sec = 0
                                    logger.info("Whisper не обнаружен, таймаут whisper_timeout_sec отключен")

                            elif msg_type == 'partial':
                                if not self._new_speech:
                                    self._new_speech = True
                                    self._event_interrupt.set()  # начали новую речь, прервать всех ассистентов

                            elif msg_type == 'result':
                                engine_name = data.get('engine')
                                request_id = data.get('request_id')

                                # --- Vosk ---
                                if engine_name == 'vosk':
                                    current_request_id = request_id
                                    vosk_received_at = perf_counter()
                                    current_answers = [data]

                                    if is_priority_command(data.get('text', '')):
                                        # Команда: обрабатывать сразу, Whisper не ждать
                                        await process_final_answers(current_answers)
                                        reset_state()

                                # --- Whisper ---
                                elif engine_name == 'whisper':
                                    # Принять только ответ на текущую фразу
                                    if request_id == current_request_id:
                                        current_answers.append(data)
                                        await process_final_answers(current_answers)
                                        reset_state()
                            # --- Таймаут Whisper ---
                            if vosk_received_at is not None and (
                                    perf_counter() - vosk_received_at) > whisper_timeout_sec:
                                if current_answers:
                                    await process_final_answers(current_answers)
                                reset_state()
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
