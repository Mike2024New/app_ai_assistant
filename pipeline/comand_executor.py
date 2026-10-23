import sys
import subprocess
from pathlib import Path
from config import commands, logger

from infrastructure_path_utils import find_interpreter_by_root_dir, get_root_dir_path

LOG_NAME = 'COMMAND_EXECUTOR'


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
        logger.info(f'[ {LOG_NAME} ] Выполнение команды `{cmd_name}` для скрипта `{file}`')
        answer = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.debug(f'[ comand_executor ] Команда не выполнена, время ожидания превышено.')
        return 'Команда не выполнена, превышено время ожидания.'

    stdout_text = answer.stdout.decode('utf-8', errors='replace').strip() if answer.stdout else ''
    stderr_text = answer.stderr.decode('utf-8', errors='replace').strip() if answer.stderr else ''

    # инфо о выполненной команде
    logger.debug(f'[ {LOG_NAME} ] DEBUG: returncode={answer.returncode}')
    if answer.returncode != 0:
        return 'Ошибка при выполнении команды.'  # сообщение для ассистента
    res = stderr_text or stdout_text or None
    return res


if __name__ == '__main__':
    print(executor('открой компьютер'))
