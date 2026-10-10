import asyncio
from config import settings
from moduls import Launcher
from pipeline import Pipeline
from infrastructure_path_utils import get_root_dir_path


async def main():
    async def observer(queue_dialog):
        while True:
            try:
                res = await asyncio.wait_for(queue_dialog.get(), 0.5)
                if res is None:
                    break
                print(res)
            except asyncio.TimeoutError:
                pass

    queue = asyncio.Queue()
    launcher = Launcher(target_dir=get_root_dir_path())
    await launcher.start(services=settings.services, log_level='info')
    pipeline = Pipeline(services=launcher.run_services, queue_dialog=queue)
    await pipeline.start()
    asyncio.create_task(observer(queue_dialog=queue))
    await asyncio.to_thread(lambda: input('...'))
    await pipeline.stop()
    await launcher.stop()


if __name__ == '__main__':
    asyncio.run(main())
