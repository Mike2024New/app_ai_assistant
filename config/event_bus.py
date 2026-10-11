import asyncio, json
from infrastructure_other import TimeUtils
from pathlib import Path


class EventBus:
    def __init__(self, log_file_path: Path, maxsize: int = 1000):
        self._lock = asyncio.Lock()
        self._log_file_path = log_file_path
        self._messages = asyncio.Queue(maxsize=maxsize)
        self._time_utils = TimeUtils()

    def log_message(self, message):
        with open(self._log_file_path, mode='a', encoding='utf-8') as f:
            row = {'message': message, 'timestamp': self._time_utils.timestamp()}
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

    async def add_message(self, message):
        # точка записи сообщения в лог-файл
        await asyncio.to_thread(lambda: self.log_message(message=message))
        await self._messages.put(message)

    async def get_message(self):
        try:
            message = self._messages.get_nowait()
            return message
        except asyncio.QueueEmpty:
            return None


async def main():
    evbus = EventBus(log_file_path=Path('log.jsonl'))
    await evbus.add_message(message='Демо')
    print(await evbus.get_message())
    print(await evbus.get_message())


if __name__ == '__main__':
    asyncio.run(main())
