from pydantic import BaseModel
from typing import Any


class Settings(BaseModel):
    app_name: str = 'app'
    services: dict[str, Any]
