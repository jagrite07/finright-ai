# ============================================================
# FinRight AI — app/config.py
#
# Loads all settings from the .env file.
# Use anywhere: from app.config import settings
#
# TO CHANGE A SETTING: edit .env, not this file.
# ============================================================

from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # App info
    app_name: str = "FinRight AI"
    app_version: str = "1.0.0"
    app_env: str = "development"
    secret_key: str = "change-in-production"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allowed_origins: str = "*"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Shortcut import
settings = get_settings()
