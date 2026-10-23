import json
from infrastructure_path_utils import get_root_dir_path

"""При первом запуске, инициализация демонстрационных скриптов"""

# базовый скрипт
script = """import sys, os
from pathlib import Path

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

scripts_json = {
    "открой рабочий стол": {
        "file": "scripts/demo.py",
        "args": [
            "desktop"
        ],
        "timeout": 10
    },
    "открой компьютер": {
        "file": "scripts/demo.py",
        "args": [
            "computer"
        ],
        "timeout": 10
    },
    "открой папку": {
        "file": "scripts/demo.py",
        "args": [
            "C:/Users"
        ],
        "timeout": 10
    }
}


def create_scripts_folder():
    scripts_folder = get_root_dir_path() / 'scripts'
    if not scripts_folder.exists():
        scripts_folder.mkdir(exist_ok=True, parents=True)

    scripts_file = scripts_folder / 'demo.py'
    if not scripts_file.exists():
        # создание файла со скриптами (базовое открытие папок)
        with open(file=scripts_file, mode='w', encoding='utf-8') as f:
            f.write(script)

    scripts_json_file = get_root_dir_path() / 'scripts.json'
    if not scripts_json_file.exists():
        # создание json со скриптами
        with open(scripts_json_file, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(scripts_json, ensure_ascii=False, indent=2))
