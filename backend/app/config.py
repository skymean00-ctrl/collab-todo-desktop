from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # DB
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "collab_todo"

    # JWT
    secret_key: str = ""  # 반드시 .env에서 설정 필요
    access_token_expire_minutes: int = 480

    # CORS (쉼표 구분, 예: https://todo.example.com,null)
    # null은 Electron 앱에서 사용. 배포 시 실제 도메인으로 제한할 것.
    allowed_origins: List[str] = ["*"]

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
    app_base_url: str = "http://localhost:5173"  # 인증 메일 링크용 (배포 시 실제 주소로 변경)

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if not v:
            raise ValueError("SECRET_KEY는 반드시 .env에서 설정해야 합니다.")
        return v

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
