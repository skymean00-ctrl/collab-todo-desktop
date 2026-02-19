"""사용자 데이터 접근."""

from __future__ import annotations

from typing import List, Optional

from mysql.connector.connection import MySQLConnection

from collab_todo.models import User


def _row_to_user(row: tuple) -> User:
    return User(
        id=row[0],
        username=row[1],
        display_name=row[2],
        email=row[3],
        job_title=row[4],
        role=row[5],
        is_active=bool(row[6]),
        created_at=row[7],
        updated_at=row[8],
    )


def get_user_by_id(conn: MySQLConnection, user_id: int) -> Optional[User]:
    if user_id <= 0:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, username, display_name, email, job_title, role, is_active,
                   created_at, updated_at
              FROM users
             WHERE id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return None
    return _row_to_user(row)


def get_user_by_username(conn: MySQLConnection, username: str) -> Optional[User]:
    """로그인용: username으로 사용자 조회."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, username, display_name, email, job_title, role, is_active,
                   created_at, updated_at
              FROM users
             WHERE username = %s
            """,
            (username,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return None
    return _row_to_user(row)


def get_password_hash(conn: MySQLConnection, username: str) -> Optional[str]:
    """로그인 인증용: password_hash만 조회."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT password_hash FROM users WHERE username = %s",
            (username,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return None
    return row[0]


def list_active_users(conn: MySQLConnection) -> List[User]:
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, username, display_name, email, job_title, role, is_active,
                   created_at, updated_at
              FROM users
             WHERE is_active = 1
             ORDER BY display_name ASC
            """
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_user(row) for row in rows]


def list_pending_users(conn: MySQLConnection) -> List[User]:
    """관리자용: 승인 대기 중인 사용자 목록."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, username, display_name, email, job_title, role, is_active,
                   created_at, updated_at
              FROM users
             WHERE is_active = 0
             ORDER BY created_at ASC
            """
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_user(row) for row in rows]


def create_user(
    conn: MySQLConnection,
    *,
    username: str,
    display_name: str,
    email: str,
    job_title: str = "",
    password_hash: str,
) -> int:
    """가입 신청: is_active=0 상태로 생성."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (username, display_name, email, job_title, password_hash, is_active)
            VALUES (%s, %s, %s, %s, %s, 0)
            """,
            (username, display_name, email, job_title, password_hash),
        )
        user_id = cursor.lastrowid
    finally:
        cursor.close()

    return user_id


def activate_user(conn: MySQLConnection, user_id: int) -> None:
    """관리자 승인: is_active=1로 변경."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET is_active = 1 WHERE id = %s",
            (user_id,),
        )
    finally:
        cursor.close()


def deactivate_user(conn: MySQLConnection, user_id: int) -> None:
    """관리자 거절/비활성화."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET is_active = 0 WHERE id = %s",
            (user_id,),
        )
    finally:
        cursor.close()
