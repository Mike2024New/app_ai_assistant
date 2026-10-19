import asyncio, json
from infrastructure_path_utils import get_root_dir_path
from pathlib import Path


class EventBus:
    def __init__(self, log_file_path: Path, log_file: bool = True, maxsize: int = 1000):
        self._lock = asyncio.Lock()
        self._log_file_path = log_file_path
        self._log_file = log_file
        self._messages = asyncio.Queue(maxsize=maxsize)

    def log_message(self, message: dict):
        if not self._log_file:
            return
        with open(self._log_file_path, mode='a', encoding='utf-8') as f:
            f.write(json.dumps(message, ensure_ascii=False) + '\n')

    async def add_message(self, message: dict):
        await asyncio.to_thread(lambda: self.log_message(message=message))
        await self._messages.put(message)

    async def get_message(self):
        try:
            message = self._messages.get_nowait()
            return message
        except asyncio.QueueEmpty:
            return None


async def main():
    from infrastructure_other import TimeUtils
    time_utils = TimeUtils()

    evbus = EventBus(log_file_path=get_root_dir_path() / 'log.jsonl', log_file=False)
    await evbus.add_message(message={'message': 'demo', 'timestamp': time_utils.timestamp()})
    print(await evbus.get_message())
    print(await evbus.get_message())


if __name__ == '__main__':
    asyncio.run(main())
