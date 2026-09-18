import asyncio
# from pathlib import Path
from config import settings
from moduls import Launcher
from pipeline import Pipeline
from infrastructure_path_utils import get_root_dir_path


async def main():
    # launcher = Launcher(target_dir=Path(r'C:\Users\projects\Desktop\demo'))
    launcher = Launcher(target_dir=get_root_dir_path())
    await launcher.start(services=settings.services, log_level='info')
    pipeline = Pipeline(services=launcher.run_services)
    await pipeline.start()  # запуск конвейрера (комбинации сервисов)
    await asyncio.to_thread(lambda: input('...press enter for exti...'))
    await pipeline.stop()  # остановить конвейер (комбинации сервисов)
    await launcher.stop()  # остановить сервера


if __name__ == '__main__':
    asyncio.run(main())
