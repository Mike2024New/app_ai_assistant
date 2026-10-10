import asyncio
from launcher import Launcher
from pipeline import Pipeline

"""
Терминальная, cmd версия. Сборка всего пайплайна, управление настройками через правку settings.json
"""


async def main():
    async def observer(queue_dialog: asyncio.Queue):
        last_role = 'user'
        while True:
            try:
                res = await asyncio.wait_for(queue_dialog.get(), 0.5)
                if res is None:
                    break
                # сборка и обработка сообщений для терминальной версии
                if res.get('role') == 'user':
                    if last_role != 'user':
                        print()
                    print(f"[ user ] {res.get('text')}")
                if res.get('role') == 'ai':
                    # Так как ИИ выдает весь текст не сразу а порциями, то сборка идет здесь
                    if last_role != 'ai':
                        print(f'[ AI ]', end=' ')
                    print(f"{res.get('text')}", end=' ')

                last_role = res.get('role')  # обновление последней роли
            except asyncio.TimeoutError:
                pass

    async def observer_launcher(queue_launch: asyncio.Queue):
        while True:
            try:
                res = await asyncio.wait_for(queue_launch.get(), 0.5)
                if res is None:
                    break
                print(res)
            except asyncio.TimeoutError:
                pass

    queue_launcher = asyncio.Queue()
    queue_pipeline = asyncio.Queue()
    launcher = Launcher(queue_launcher=queue_launcher)
    asyncio.create_task(observer_launcher(queue_launch=queue_launcher))
    await launcher.start()
    pipeline = Pipeline(services=launcher.run_services, queue_dialog=queue_pipeline)
    await pipeline.start()
    asyncio.create_task(observer(queue_dialog=queue_pipeline))
    await asyncio.to_thread(lambda: input('...'))
    await asyncio.sleep(5)
    await pipeline.stop()
    await launcher.stop()


if __name__ == '__main__':
    asyncio.run(main())
