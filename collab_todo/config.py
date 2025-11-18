"""
애플리케이션 설정 로딩 모듈.

환경 변수 또는 .env 파일을 통해 DB 연결 정보를 안전하게 읽어온다.
코드 레벨에서 하드코딩된 비밀번호를 사용하지 않도록 한다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


_ENV_PREFIX = "COLLAB_TODO_"


@dataclass(frozen=True)
class DatabaseConfig:
    """데이터베이스 연결에 필요한 최소 설정 값."""

    host: str
    port: int
    user: str
    password: str
    database: str
    use_ssl: bool = False


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


def load_db_config() -> Optional[DatabaseConfig]:
    """
    환경 변수에서 DB 설정을 읽어 DatabaseConfig로 반환한다.

    필수 값 중 하나라도 없으면 None을 반환하여 호출 측에서
    '설정 미완료' 상태를 구분할 수 있게 한다.
    """
    host = _get_env("DB_HOST")
    port_str = _get_env("DB_PORT")
    user = _get_env("DB_USER")
    password = _get_env("DB_PASSWORD")
    database = _get_env("DB_NAME")
    use_ssl_str = _get_env("DB_USE_SSL")

    if not (host and port_str and user and password and database):
        return None

    try:
        port = int(port_str)
        if port <= 0 or port > 65535:
            # 포트 범위 벗어나는 경우는 잘못된 설정으로 간주
            return None
    except ValueError:
        return None

    use_ssl = (use_ssl_str or "").lower() in {"1", "true", "yes", "on"}

    return DatabaseConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        use_ssl=use_ssl,
    )


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
            # 잘못된 값이면 기본값 사용
            timeout = 15

    return AiServiceConfig(
        base_url=base_url,
        api_key=api_key,
        timeout_seconds=timeout,
    )



