from infrastructure_path_utils import get_root_dir_path
from infrastructure_settings_manager import get_settings_manager
from config.schemas import Settings
from infrastructure_other.time_utils import TimeUtils
from config.default_settings import default_settings
from infrastructure_log_utils import Logger
import sys, uuid

__all__ = [
    'settings', 'settings_manager',
    'time_utils', 'EXE_MODE', 'history_messages_json',
    'logger', 'request_id',
]

request_id = str(uuid.uuid4())[:8]

logger = Logger(
    log_path=get_root_dir_path() / 'logs/app.log',
    rotation='10 MB', retention=10,
    compression='zip',
    fmt='{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[request_id]} | {message}'
)

logger.set_logger(request_id=request_id)

EXE_MODE = getattr(sys, 'frozen', False)  # сейчас режим разработчика или запуск из кода?
history_messages_json = get_root_dir_path() / 'summary_messages.json'

settings_manager = get_settings_manager(
    json_file_path=get_root_dir_path() / 'settings.json',
    settings_model=Settings.model_validate(default_settings),  # взять модель по умолчанию
)

settings = settings_manager.settings
time_utils = TimeUtils(timestamp_fmt='%d.%m.%Y %H:%M:%S.%f')
