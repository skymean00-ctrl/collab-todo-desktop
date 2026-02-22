"""Alembic 환경 설정 — app.config의 Settings에서 DB URL을 읽어옵니다."""
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# backend/ 디렉토리를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.database import Base

# 모든 모델이 Base.metadata에 등록되도록 임포트
import app.models.user  # noqa: F401
import app.models.task  # noqa: F401

# Alembic Config object
config = context.config

# 로깅 설정 (alembic.ini)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# app.config에서 DB URL 읽기 (.env 파일 기반)
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드: SQL 스크립트 출력만 (DB 연결 불필요)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드: 실제 DB에 연결하여 마이그레이션 수행."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
