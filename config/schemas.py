from pydantic import BaseModel
from typing import Any


class Settings(BaseModel):
    app_name: str = 'app_ai_assistant'
    services: dict[str, Any]
