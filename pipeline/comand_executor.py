import sys
import subprocess
from pathlib import Path
from config import commands, logger

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

    # 1. Искать .venv рядом со скриптом
    python_exe_interpr_path = find_interpreter_by_root_dir(file.parent)

    # 2. Если нет, искать .venv в корне проекта
    if python_exe_interpr_path is None:
        python_exe_interpr_path = find_interpreter_by_root_dir(get_root_dir_path())

    # 3. Если нашли .venv — использовать его без флага
    if python_exe_interpr_path is not None:
        cmd = [python_exe_interpr_path]
    else:
        # 4. Если .venv нет вообще — использовать app.exe с флагом
        cmd = [sys.executable, '--run-script']

    default_args = commands[cmd_name]['args'] if not args else args
    timeout = commands[cmd_name]['timeout']
    cmd.extend([str(file), *default_args])

    try:
        answer = subprocess.run(cmd, capture_output=True, timeout=timeout, encoding='utf-8')
    except subprocess.TimeoutExpired:
        return 'Команда не выполнена, превышено время ожидания.'
    if answer.returncode != 0:
        print(answer)
        logger.error(f'[ comand_executor ] Ошибка при выплонении команды `{cmd_name}`: return_code!=0 {answer.stderr}')
        return 'Ошибка при выполнении команды.'  # сообщение для ассистента
    res = answer.stdout.strip()
    return res or None  # вернуть ассистенту  ответ если есть


if __name__ == '__main__':
    print(executor('открой компьютер'))
