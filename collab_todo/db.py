"""
MySQL 데이터베이스 연결 모듈.

이 모듈은 연결 생성/종료 책임만 가지며, 쿼리 로직은 별도 레이어에서 구현한다.
널 포인터, 자원 누수, 예외적인 연결 오류를 최소화하기 위해 방어적으로 작성한다.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

import mysql.connector
from mysql.connector.connection import MySQLConnection

from .config import DatabaseConfig, load_db_config


class DatabaseConnectionError(Exception):
    """DB 연결에 실패했을 때 사용하는 애플리케이션 전용 예외."""


def create_connection(config: Optional[DatabaseConfig] = None) -> MySQLConnection:
    """
    DatabaseConfig를 기반으로 MySQLConnection을 생성한다.

    - 설정이 없으면 DatabaseConnectionError를 발생시킨다.
    - 내부적으로 mysql.connector.connect에서 발생하는 예외를 감싸서 전달한다.
    """
    effective_config = config or load_db_config()
    if effective_config is None:
        raise DatabaseConnectionError(
            "데이터베이스 설정이 완료되지 않았습니다. "
            "환경 변수 COLLAB_TODO_DB_HOST 등 설정을 확인하세요."
        )

    connect_args = {
        "host": effective_config.host,
        "port": effective_config.port,
        "user": effective_config.user,
        "password": effective_config.password,
        "database": effective_config.database,
        "autocommit": False,
    }

    if effective_config.use_ssl:
        connect_args["ssl_disabled"] = False

    try:
        conn: MySQLConnection = mysql.connector.connect(**connect_args)
    except mysql.connector.Error as exc:  # pragma: no cover - 구체 환경 의존
        # 여기서 직접 비밀번호를 로그에 남기지 않도록 주의한다.
        raise DatabaseConnectionError(f"데이터베이스 연결 실패: {exc}") from exc

    if not conn.is_connected():
        # 연결 객체가 생성되었지만 실제 연결이 안 된 경우를 방어
        conn.close()
        raise DatabaseConnectionError("데이터베이스에 연결되지 않았습니다.")

    return conn


@contextmanager
def db_connection(
    config: Optional[DatabaseConfig] = None,
) -> Generator[MySQLConnection, None, None]:
    """
    with 문으로 안전하게 사용할 수 있는 DB 연결 컨텍스트 매니저.

    예:
        with db_connection() as conn:
            # 쿼리 실행

    - 블록 내에서 예외가 발생하면 롤백 후 연결을 닫는다.
    - 정상 종료 시 커밋 후 연결을 닫는다.
    - 연결은 finally 블록에서 반드시 닫힌다.
    """
    conn = create_connection(config)
    exc_occurred = False
    try:
        yield conn
    except Exception:
        exc_occurred = True
        try:
            conn.rollback()
        except mysql.connector.Error:
            pass
        raise
    else:
        try:
            conn.commit()
        except mysql.connector.Error:
            conn.rollback()
            raise
    finally:
        conn.close()


