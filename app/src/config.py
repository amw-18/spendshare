from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr
from typing import List, Union

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./main.db"
    DATABASE_ECHO: bool = False

    # CORS
    CORS_ALLOWED_ORIGINS_STRING: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def CORS_ALLOWED_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS_STRING.split(",")]

    # API metadata
    API_TITLE: str = "SpendShare API"
    API_DESCRIPTION: str = "API for managing expenses, users, and groups."
    API_VERSION: str = "0.1.0"

    # Support Email
    SUPPORT_EMAIL: EmailStr = "amw@spendshare.app"

    # JWT Settings (common for APIs, add if you use JWT)
    SECRET_KEY: str = "your_super_secret_key_here_please_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

settings = Settings()
