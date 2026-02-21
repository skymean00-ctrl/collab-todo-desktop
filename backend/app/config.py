from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DB
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "collab_todo"

    # JWT
    secret_key: str = "change-this-secret"
    access_token_expire_minutes: int = 480

    # Email
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_server: str = "smtp.gmail.com"
    mail_port: int = 587

    # File storage
    file_storage_path: str = "./uploads"

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
