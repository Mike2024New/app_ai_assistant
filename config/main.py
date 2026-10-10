from infrastructure_path_utils import get_root_dir_path
from infrastructure_settings_manager import get_settings_manager
from config.schemas import Settings
from infrastructure_other.time_utils import TimeUtils
import sys

__all__ = ['settings', 'settings_manager', 'time_utils', 'EXE_MODE']

EXE_MODE = getattr(sys, 'frozen', False)  # сейчас режим разработчика или запуск из кода?

settings_manager = get_settings_manager(
    json_file_path=get_root_dir_path() / 'settings.json',
    settings_model=Settings(services={}),
)

settings = settings_manager.settings
time_utils = TimeUtils(timestamp_fmt='%d.%m.%Y %H:%M:%S.%f')
