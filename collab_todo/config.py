"""
애플리케이션 설정 로딩 모듈.

환경 변수 또는 기본값을 통해 SQLite DB 경로와 AI 서비스 설정을 읽어온다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


_ENV_PREFIX = "COLLAB_TODO_"


@dataclass(frozen=True)
class DatabaseConfig:
    """SQLite 데이터베이스 파일 경로 설정."""

    db_path: str


@dataclass(frozen=True)
class AiServiceConfig:
    """AI 요약 서비스 설정 값."""

    base_url: str
    api_key: Optional[str]
    timeout_seconds: int = 15


def _get_env(name: str) -> Optional[str]:
    """환경 변수 값을 읽되, 공백 문자열은 None으로 처리한다."""
    raw = os.getenv(f"{_ENV_PREFIX}{name}")
    if raw is None:
        return None
    value = raw.strip()
    return value or None


def load_db_config() -> DatabaseConfig:
    """
    환경 변수 COLLAB_TODO_DB_PATH 에서 SQLite 파일 경로를 읽는다.

    설정이 없으면 홈 디렉터리 아래 기본 경로를 사용한다.
    """
    path = _get_env("DB_PATH")
    if not path:
        path = str(Path.home() / ".collab_todo" / "collab_todo.db")
    return DatabaseConfig(db_path=path)


def load_ai_service_config() -> Optional[AiServiceConfig]:
    """
    환경 변수에서 AI 서비스 설정을 읽어 AiServiceConfig로 반환한다.

    필수 값(base_url)이 없으면 None을 반환한다.
    """
    base_url = _get_env("AI_BASE_URL")
    api_key = _get_env("AI_API_KEY")
    timeout_str = _get_env("AI_TIMEOUT_SECONDS")

    if not base_url:
        return None

    timeout = 15
    if timeout_str:
        try:
            parsed = int(timeout_str)
            if parsed > 0:
                timeout = parsed
        except ValueError:
            timeout = 15

    return AiServiceConfig(
        base_url=base_url,
        api_key=api_key,
        timeout_seconds=timeout,
    )
