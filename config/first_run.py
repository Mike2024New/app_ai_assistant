import json
from infrastructure_path_utils import get_root_dir_path

"""При первом запуске, инициализация демонстрационных скриптов"""

# базовый скрипт
script = """import sys, os
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

additionally_json = {
    "additionally": [
        {
            "srv": "srv_llm",
            "label": "gemma-3-1b-it-Q4_K_M.gguf",
            "relative_path_file": "srv_llm/resources/models/gemma-3-1b-it-Q4_K_M.gguf",
            "url": "https://huggingface.co/lmstudio-community/gemma-3-1b-it-GGUF/resolve/main/gemma-3-1b-it-Q4_K_M.gguf",
            "source": "https://huggingface.co/lmstudio-community/gemma-3-1b-it-GGUF",
            "description": "llm мозг ассистента, если у вас слабый ПК, попробуйте эту модель.",
            "continue": False
        },
        {
            "srv": "srv_llm",
            "label": "gemma-4-26B-A4B-it-Q4_K_M.gguf",
            "relative_path_file": "srv_llm/resources/models/gemma-4-26B-A4B-it-Q4_K_M.gguf",
            "url": "https://huggingface.co/lmstudio-community/gemma-4-26B-A4B-it-GGUF/resolve/main/gemma-4-26B-A4B-it-Q4_K_M.gguf",
            "source": "https://huggingface.co/lmstudio-community/gemma-4-26B-A4B-it-Q4_K_M.gguf",
            "description": "llm  ~ 16 GB.",
            "continue": False
        }
    ]
}


def create_scripts_folder():
    scripts_folder = get_root_dir_path() / 'scripts'
    if not scripts_folder.exists():
        scripts_folder.mkdir(exist_ok=True, parents=True)

    # создание файла со скриптами (базовое открытие папок)
    scripts_file = scripts_folder / 'demo.py'
    if not scripts_file.exists():
        with open(file=scripts_file, mode='w', encoding='utf-8') as f:
            f.write(script)

    # создание json со базовыми скриптами
    scripts_json_file = get_root_dir_path() / 'scripts.json'
    if not scripts_json_file.exists():
        with open(scripts_json_file, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(scripts_json, ensure_ascii=False, indent=2))

    # создание файла с доп материалами для загрузки
    additionally_json_file = get_root_dir_path() / 'additionally.json'
    if not additionally_json_file.exists():
        with open(additionally_json_file, mode='w', encoding='utf-8') as f:
            f.write(json.dumps(additionally_json, ensure_ascii=False, indent=2))
