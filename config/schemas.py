from pydantic import BaseModel, Field
from typing import Any, Literal


class Settings(BaseModel):
    app_name: str = 'app'
    theme: Literal['dark', 'light'] = 'light'
    speakers: dict[str, str] = {'en': 'en_101', 'ru': 'xenia'}
    services: dict[str, Any]
    assets: dict[str, list[dict[str, list[str]]]] = Field(default_factory=dict)
