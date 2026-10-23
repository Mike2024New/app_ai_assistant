import shutil
from pathlib import Path

from infrastructure_path_utils import get_root_dir_path, create_zip_func


def log_colapse() -> Path:
    """Рекурсивная сборка логов сервисов приложения в одну точку (на 1 папку вверх относительно корня), в 1 zip архив. Возвращает путь к файлу"""
    root_dir = get_root_dir_path()
    temp_logs_dir = root_dir.parent / 'logs_all'
    temp_logs_dir.mkdir(exist_ok=True, parents=True)

    for file in root_dir.parent.rglob('*.log'):
        if file.parent.name == 'logs':
            safe_name = file.parent.parent.name.replace(':', '_').replace('\\', '_').replace('/', '_')
            new_path = temp_logs_dir / f'{safe_name}.log'
            shutil.copy2(src='\\\\?\\' + str(file), dst='\\\\?\\' + str(new_path))

    zip_file_path = root_dir.parent / f'logs.zip'
    create_zip_func(
        source_dir=temp_logs_dir,
        target_zip=zip_file_path
    )
    shutil.rmtree('\\\\?\\' + str(temp_logs_dir))
    return zip_file_path


if __name__ == '__main__':
    print(log_colapse())
