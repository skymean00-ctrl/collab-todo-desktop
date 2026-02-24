import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_use_ssl: bool
    jwt_secret: str
    jwt_expire_hours: int


def get_settings() -> Settings:
    return Settings(
        db_host=os.environ["COLLAB_TODO_DB_HOST"],
        db_port=int(os.getenv("COLLAB_TODO_DB_PORT", "3306")),
        db_user=os.environ["COLLAB_TODO_DB_USER"],
        db_password=os.environ["COLLAB_TODO_DB_PASSWORD"],
        db_name=os.getenv("COLLAB_TODO_DB_NAME", "collab_todo"),
        db_use_ssl=os.getenv("COLLAB_TODO_DB_USE_SSL", "false").lower() == "true",
        jwt_secret=os.environ["COLLAB_TODO_JWT_SECRET"],
        jwt_expire_hours=int(os.getenv("COLLAB_TODO_JWT_EXPIRE_HOURS", "720")),
    )
