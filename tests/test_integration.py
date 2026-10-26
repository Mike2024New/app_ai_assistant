import asyncio
from launcher.launcher import Launcher


async def test_integration():
    """Проверка что сервера запускаются"""
    launcher = Launcher()
    await launcher.start()
    await asyncio.sleep(2)
    await launcher.stop()
