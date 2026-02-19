"""인증 서비스: 로그인, 가입, 비밀번호 해싱."""

from __future__ import annotations

import hashlib
import os
from typing import Optional

from mysql.connector.connection import MySQLConnection

from collab_todo.models import User
from collab_todo.repositories import (
    get_user_by_username,
    get_password_hash,
    create_user,
)


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """SHA-256 + salt 기반 비밀번호 해싱."""
    if salt is None:
        salt = os.urandom(32)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + pw_hash.hex()


def _verify_password(password: str, stored_hash: str) -> bool:
    """저장된 해시와 입력 비밀번호 비교."""
    try:
        salt_hex, hash_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return pw_hash.hex() == hash_hex
    except (ValueError, AttributeError):
        return False


def login(conn: MySQLConnection, username: str, password: str) -> Optional[User]:
    """
    로그인 시도.

    Returns:
        인증 성공 시 User, 실패 시 None.
        is_active=0이면 None 반환 (승인 대기).
    """
    stored_hash = get_password_hash(conn, username)
    if stored_hash is None:
        return None

    if not _verify_password(password, stored_hash):
        return None

    user = get_user_by_username(conn, username)
    if user is None or not user.is_active:
        return None

    return user


def check_pending(conn: MySQLConnection, username: str, password: str) -> bool:
    """비밀번호는 맞지만 승인 대기 상태인지 확인."""
    stored_hash = get_password_hash(conn, username)
    if stored_hash is None:
        return False

    if not _verify_password(password, stored_hash):
        return False

    user = get_user_by_username(conn, username)
    return user is not None and not user.is_active


def register(
    conn: MySQLConnection,
    *,
    username: str,
    display_name: str,
    password: str,
    email: str = "",
    job_title: str = "",
) -> int:
    """
    가입 신청. is_active=0으로 생성됨.

    Raises:
        ValueError: 아이디 중복 등
    """
    existing = get_user_by_username(conn, username)
    if existing is not None:
        raise ValueError("이미 사용 중인 아이디입니다.")

    password_hash = _hash_password(password)

    user_id = create_user(
        conn,
        username=username,
        display_name=display_name,
        email=email,
        job_title=job_title,
        password_hash=password_hash,
    )

    return user_id
