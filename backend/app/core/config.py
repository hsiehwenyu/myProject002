from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./invest.db"
    APP_PORT: int = 8001
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:5174"]'
    SECRET_KEY: str = "change-me-in-production-please"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin1234"

    def get_cors_origins(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
