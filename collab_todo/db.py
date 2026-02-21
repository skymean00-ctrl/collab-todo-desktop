"""
SQLite 데이터베이스 연결 모듈.

이 모듈은 연결 생성/종료 책임만 가지며, 쿼리 로직은 별도 레이어에서 구현한다.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

from .config import DatabaseConfig, load_db_config


class DatabaseConnectionError(Exception):
    """DB 연결에 실패했을 때 사용하는 애플리케이션 전용 예외."""


# datetime 타입 자동 변환 등록 (모듈 로드 시 1회)
sqlite3.register_adapter(datetime, lambda d: d.isoformat(" "))
sqlite3.register_converter(
    "DATETIME",
    lambda b: datetime.fromisoformat(b.decode()),
)
sqlite3.register_converter(
    "TIMESTAMP",
    lambda b: datetime.fromisoformat(b.decode()),
)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """테이블이 없으면 초기 스키마를 생성한다."""
    schema_path = Path(__file__).parent.parent / "sql" / "schema_sqlite.sql"
    if schema_path.exists():
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()


def create_connection(config: DatabaseConfig | None = None) -> sqlite3.Connection:
    """
    DatabaseConfig를 기반으로 sqlite3.Connection을 생성한다.
    DB 파일이 없으면 자동으로 생성하고 스키마를 초기화한다.
    """
    effective_config = config or load_db_config()

    db_path = Path(effective_config.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(
            str(db_path),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.Error as exc:
        raise DatabaseConnectionError(f"데이터베이스 연결 실패: {exc}") from exc

    _ensure_schema(conn)
    return conn


@contextmanager
def db_connection(
    config: DatabaseConfig | None = None,
) -> Generator[sqlite3.Connection, None, None]:
    """
    with 문으로 안전하게 사용할 수 있는 DB 연결 컨텍스트 매니저.

    - 블록 내에서 예외가 발생하면 롤백 후 연결을 닫는다.
    - 정상 종료 시 커밋 후 연결을 닫는다.
    """
    conn = create_connection(config)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
