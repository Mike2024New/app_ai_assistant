demo_files_script = """import sys, os
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.stdout = sys.stderr

args = sys.argv


def start():
    select = args[1] if len(args) > 1 else None
    if select == 'desktop':
        print(f'Открываю рабочий стол')
        desktop_path = Path.home() / 'Desktop'
        os.startfile(desktop_path)
    elif select == 'computer':
        print(f'Открываю компьютер')
        os.system('explorer /select,"This PC"')
    else:
        if Path(select).exists():
            os.startfile(select)
            print('открываю папку')
        else:
            print(f'Указанный путь не найден')


if __name__ == '__main__':
    start()
"""

demo_browser_script = """import webbrowser
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.stdout = sys.stderr

args = sys.argv


def start():
    url = args[1] if len(args) > 1 else None
    if url is not None:
        try:
            res = webbrowser.open(url)
            if res:
                print(f'Открываю страницу')
            else:
                print(f'Не удалось открыть страницу')
        except Exception:  # noqa
            print(f'Ошибка выполнения команды')
    else:
        print(f'Не передана ссылка')


if __name__ == '__main__':
    start()
"""

scripts_json = {
    "открой рабочий стол": {
        "file": "scripts/demo_files.py",
        "timeout": 10.0,
        "args": [
            "desktop"
        ]
    },
    "открой компьютер": {
        "file": "scripts/demo_files.py",
        "timeout": 10.0,
        "args": [
            "computer"
        ]
    },
    "открой папку": {
        "file": "scripts/demo_files.py",
        "timeout": 10.0,
        "args": [
            "C:/Users"
        ]
    },
    "открой Хабр": {
        "file": "scripts/demo_browser.py",
        "timeout": 10.0,
        "args": [
            "https://habr.com/ru/"
        ]
    }
}
