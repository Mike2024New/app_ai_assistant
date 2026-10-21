from pydantic import BaseModel
from typing import Any


class Settings(BaseModel):
    app_name: str = 'app'
    companion: bool = True
    assistant: bool = True
    whisper_timeout_sec: float = 1
    assistant_name: str = 'ассистент'
    stt_numbers_filter: bool = True
    speakers: dict[str, str] = {'en': 'en_101', 'ru': 'xenia'}
    services: dict[str, Any]
