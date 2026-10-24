import asyncio

from infrastructure_http_clients.file_downloader_v3 import DownloadTask, downolad_many_files
from infrastructure_path_utils import get_root_dir_path
from config import logger

window_name = 'additionally_downloader'


async def download_file(addon: dict, event: asyncio.Event, feedback_dict: dict | None):
    """Загрузка файла"""
    task = DownloadTask(
        label=addon['label'],
        url=addon['url'],
        relative_path_file=addon['relative_path_file'],
    )
    feedback_dict[addon['label']] = {'progress': 0.0, 'total': 0, 'downolad': 0}
    try:
        await downolad_many_files(
            event=event,
            root_dir=get_root_dir_path().parent,  # на директорию вверх
            dwn_tasks=[task],
            limit_tasks=1,
            retries=10,
            retries_timeout=5,
            retries_callback=lambda msg: logger.info(f"[ {window_name} ] {msg}"),
            error_callback=lambda msg: logger.error(f"[ {window_name} ] {msg}"),
            feedback_dict=feedback_dict,
        )
    except Exception as err:
        if not event.is_set():
            logger.error(f'[ {window_name} ] Ошибка при загрузке addon["label"]: {err}')
