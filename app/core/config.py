from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://user:password@db:5432/cp_db"
    #TODO: в ТЗ было ролевая модель, но пока неизвестно какая
    admin_token: str = "admin-token"
    specialist_token: str = "specialist-token"
    user_token: str = "user-token"
    upload_dir: Path = BASE_DIR / "storage" / "uploads"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
