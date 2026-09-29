import asyncio, sys, subprocess

"""
Скрипт установки и сборки проекта.
Требуется виртуальное окружение в папке .venv

Все шаги (простая установка после клонирования с git):     python start.py all
По отдельности:
  sync        - установить зависимости
  dwn         - скачать материалы
  build       - собрать .exe/bin
"""
args = sys.argv


async def start():
    if 'sync' in args or 'all' in args:
        if 'all' in args:
            print(f'Установка библиотек и зависимостей', flush=True)
        cmd = [sys.executable, '-m', 'pip', 'install', 'uv']
        subprocess.run(cmd, shell=False)
        cmd = [sys.executable, '-m', 'uv', 'sync']
        subprocess.run(cmd, shell=False)

    if 'build' in args or 'all' in args:
        if 'all' in args:
            print(f'Сборка .exe/bin', flush=True)
        cmd = [sys.executable, 'cli.py', 'build', '-oe']
        subprocess.run(cmd, shell=False)


if __name__ == '__main__':
    asyncio.run(start())
