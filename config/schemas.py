from pydantic import BaseModel, Field
from typing import Any


class Settings(BaseModel):
    app_name: str = 'app'
    speakers: dict[str, str] = {'en': 'en_101', 'ru': 'xenia'}
    services: dict[str, Any]
    assets: dict[str, list[dict[str, list[str]]]] = Field(default_factory=dict)
