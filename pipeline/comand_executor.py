import sys
import subprocess
from pathlib import Path
from config import commands

from infrastructure_path_utils import find_interpreter_by_root_dir, get_root_dir_path


def executor(cmd_name: str, *args):
    """Блок исполняющий команды, предполагается что уже точно известно какая команда выполняется
    (блок фильтрации команд должен лежать до вызова этой функции)"""

    # проверка ключей
    if 'file' not in commands[cmd_name]:
        return 'Команда не правильно прописана в джейсон, нет поля с файлом'
    if 'timeout' not in commands[cmd_name]:
        return 'Команда не правильно прописана в джейсон, нет поля таймаут'
    if 'args' not in commands[cmd_name]:
        return 'Команда не правильно прописана в джейсон, нет поля аргс'

    file = Path(commands[cmd_name]['file'])

    # отлов относительных путей если запись краткая (игнорирует абсолютные пути)
    if not file.is_absolute():
        file = get_root_dir_path() / file

    if not file.exists():
        return 'Файл с скриптом не найден'

    # поиск .venv скрипта, если его нет, то попытаться выполнить от текущего .venv
    python_exe_interpr_path = find_interpreter_by_root_dir(file.parent)
    if python_exe_interpr_path is None:
        python_exe_interpr_path = sys.executable

    default_args = commands[cmd_name]['args'] if not args else args
    timeout = commands[cmd_name]['timeout']

    cmd = [python_exe_interpr_path, file, *default_args]
    try:
        answer = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 'Команда не выполнена, превышено время ожидания.'
    if answer.returncode != 0:
        return 'Ошибка при выполнении команды.'  # сообщение для ассистента
    res = answer.stdout.decode('utf-8').strip()
    return res or None  # вернуть ассистенту  ответ если есть


if __name__ == '__main__':
    print(executor('рабочий стол', 'desktop'))
