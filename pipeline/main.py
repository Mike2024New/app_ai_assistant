import asyncio
from clients import STTClient
from clients import TTSClient
from clients import LLMClient

"""
Реализация полезной нагрузки приложения (пайплайн).
"""


class Pipeline:
    def __init__(self, services: dict[str, int]):
        self._stt = STTClient(port=services['srv_stt_vosk'])
        self._tts = TTSClient(port=services['srv_tts_silero'])
        self._llm = LLMClient(port=services['srv_llm'])
        self._event = asyncio.Event()

    async def start(self):
        asyncio.create_task(self._stt.listen(event=self._event, callback=self._callback))

    async def stop(self):
        self._event.set()

    async def _tts_callback(self, sentence):
        await self._tts.say(text=sentence, speaker='xenia', add=True)

    async def _callback(self, text):
        await self._tts.interrupt()
        await self._llm.ask_and_sentence(prompt=text, callback=self._tts_callback)


async def main():
    pipeline = Pipeline(
        services={
            'srv_llm': 8000,
            'srv_stt_vosk': 8001,
            'srv_tts_silero': 8002,
        }
    )
    await pipeline.start()
    await asyncio.to_thread(lambda: input('...press enter for exit...\n'))
    await pipeline.stop()


if __name__ == '__main__':
    asyncio.run(main())
