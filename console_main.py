import asyncio
from launcher import Launcher
from pipeline import Pipeline

"""
Терминальная, cmd версия. Сборка всего пайплайна, управление настройками через правку settings.json
"""


async def main():
    last_role = 'user'

    def pipeline_observer_callback(res):
        nonlocal last_role
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

    # запуск сервисов
    launcher = Launcher()
    asyncio.create_task(launcher.observer(callback=lambda x: print(x)))
    await launcher.start()
    # запуск пайплайна (цепочка stt->llm->tts)
    pipeline = Pipeline()
    asyncio.create_task(pipeline.observer(callback=pipeline_observer_callback))
    await pipeline.start(services=launcher.run_services)
    await asyncio.to_thread(lambda: input('...'))
    await pipeline.stop()  # остановка пайплайна
    await launcher.stop()  # остановка сервисов


if __name__ == '__main__':
    asyncio.run(main())
