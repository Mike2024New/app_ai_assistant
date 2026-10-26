import json
from infrastructure_path_utils import get_root_dir_path
from config.ini.additionally_json_temp import additionally_json
from config.ini.scripts import demo_files_script, demo_browser_script, scripts_json

"""При первом запуске, инициализация демонстрационных скриптов"""


def first_run_ini():
    scripts_folder = get_root_dir_path() / 'scripts'
    if not scripts_folder.exists():
        scripts_folder.mkdir(exist_ok=True, parents=True)

    # создание файла со скриптами (базовое открытие папок)
    scripts_file = scripts_folder / 'demo_files.py'
    if not scripts_file.exists():
        with open(file=scripts_file, mode='w', encoding='utf-8') as f:
            f.write(demo_files_script)

    # создание файла со скриптами (базовое открытие web страниц)
    scripts_file = scripts_folder / 'demo_browser.py'
    if not scripts_file.exists():
        with open(file=scripts_file, mode='w', encoding='utf-8') as f:
            f.write(demo_browser_script)

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
