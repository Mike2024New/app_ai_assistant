from pydantic import BaseModel
from typing import Any, Literal


class Settings(BaseModel):
    theme: Literal['dark', 'light'] = 'dark'
    app_name: str = 'app'
    assistant_name_in_cmd: bool = True
    companion: bool = True
    assistant: bool = True
    assistant_speech: bool = True
    whisper_timeout_sec: float = 1
    assistant_name: str = 'ассистент'
    stt_numbers_filter: bool = True
    speakers: dict[str, str] = {'en': 'en_101', 'ru': 'xenia'}
    services: dict[str, Any]
