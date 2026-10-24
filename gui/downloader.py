import asyncio

from infrastructure_http_clients.file_downloader_v3 import DownloadTask, downolad_many_files
from infrastructure_path_utils import get_root_dir_path
from config import logger

window_name = 'additionally_downloader'


async def download_file(addon: dict, event: asyncio.Event, feedback_dict: dict | None):
    """Загрузка файла"""
    event.clear()
    task = DownloadTask(
        label=addon['label'],
        url=addon['url'],
        relative_path_file=addon['relative_path_file'],
    )
    feedback_dict[addon['label']] = {'progress': 0.0, 'total': 0, 'downolad': 0}
    try:
        tasks = []
        # добавление дополнительных файлов (например для whisper нужно подгружать ещё файлы конфигураций и моделей)
        for add in addon['added']:
            feedback_dict[add['label']] = {'progress': 0.0, 'total': 0, 'downolad': 0}
            tasks.append(
                DownloadTask(
                    label=add['label'],
                    url=add['url'],
                    relative_path_file=add['relative_path_file']
                )
            )

        tasks.append(task)

        await downolad_many_files(
            event=event,
            root_dir=get_root_dir_path().parent,  # на директорию вверх
            dwn_tasks=tasks,
            limit_tasks=4,
            retries=10,
            retries_timeout=5,
            retries_callback=lambda msg: logger.info(f"[ {window_name} ] {msg}"),
            error_callback=lambda msg: logger.error(f"[ {window_name} ] {msg}"),
            feedback_dict=feedback_dict,
        )
        # загрузка завершена, убрать её
        feedback_dict.pop(addon['label'])
        for add in addon['added']:
            feedback_dict.pop(add['label'])
    except Exception as err:
        if not event.is_set():
            logger.error(f'[ {window_name} ] Ошибка при загрузке addon["label"]: {err}')
