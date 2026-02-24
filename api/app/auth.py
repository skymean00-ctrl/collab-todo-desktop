import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings
from .db import get_db

logger = logging.getLogger("auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# auto_error=False: Authorization 헤더 없을 때 403 대신 None 반환 → get_current_user에서 401 처리
bearer_scheme = HTTPBearer(auto_error=False)


def _db_bool(val) -> bool:
    """MySQL 컬럼 값을 Python bool로 안전하게 변환.

    MySQL BIT(1) → bytes (b'\\x00'/b'\\x01'), TINYINT → int, NULL → None
    모두 올바른 bool로 변환한다.
    """
    if val is None:
        return False
    if isinstance(val, (bytes, bytearray)):
        return val != b'\x00' and len(val) > 0
    return bool(val)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def create_access_token(user_id: int, username: str) -> str:
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=s.jwt_expire_hours)
    payload = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """username 또는 email + password 검증. 성공 시 user dict 반환, 실패 시 None."""
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, display_name, email, password_hash, department, role, is_active, is_deleted "
            "FROM users WHERE username = %s OR email = %s",
            (username, username),
        )
        user = cursor.fetchone()
        cursor.close()

    if not user or not _db_bool(user["is_active"]) or _db_bool(user.get("is_deleted")):
        return None
    if not user["password_hash"] or not verify_password(password, user["password_hash"]):
        return None
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """JWT 토큰 검증 → 현재 사용자 반환. 모든 보호된 엔드포인트에서 사용."""
    if not credentials:
        print("[AUTH-FAIL] no credentials (Authorization header missing)", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다. 다시 로그인해주세요.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    s = get_settings()
    token = credentials.credentials
    token_preview = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else token
    try:
        payload = jwt.decode(token, s.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
        username: str = payload["username"]
    except (JWTError, KeyError, ValueError) as e:
        print(f"[AUTH-FAIL] JWT decode error: {e} token={token_preview}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 유효하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 로그인 시점에 is_active/is_deleted를 이미 검증했으므로
    # 매 요청마다 DB를 재확인하지 않고 JWT만 신뢰한다.
    # (토큰 만료 시 자연스럽게 재로그인 필요)
    return {"id": user_id, "username": username}
