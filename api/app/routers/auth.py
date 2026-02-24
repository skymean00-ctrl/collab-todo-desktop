import re
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import authenticate_user, create_access_token, hash_password, get_current_user, verify_password
from ..db import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str = ""
    department: str = ""
    job_title: str = ""
    is_admin: bool = False
    is_verified: bool = True


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    department_name: str = ""


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str
    department: str = ""
    job_title: str = ""
    is_admin: bool = False
    is_verified: bool = False


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    user = authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
        )
    token = create_access_token(user["id"], user["username"])
    return LoginResponse(
        access_token=token,
        user_id=user["id"],
        name=user["display_name"],
        email=user.get("email", ""),
        department=user.get("department", ""),
        is_admin=(user.get("role") == "admin"),
    )


@router.post("/register", response_model=RegisterResponse)
def register(body: RegisterRequest):
    # 이메일에서 username 생성 (@ 앞부분, 특수문자 제거)
    username = re.sub(r"[^a-zA-Z0-9_]", "_", body.email.split("@")[0])[:50]

    password_hash = hash_password(body.password)

    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)

        # 이메일 중복 확인
        cursor.execute("SELECT id FROM users WHERE email = %s", (body.email,))
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 이메일입니다.",
            )

        # username 중복 시 숫자 붙이기
        base = username
        for i in range(1, 100):
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if not cursor.fetchone():
                break
            username = f"{base}_{i}"

        cursor.execute(
            """INSERT INTO users (username, display_name, email, password_hash, department, role, is_active)
               VALUES (%s, %s, %s, %s, %s, 'user', 1)""",
            (username, body.name, body.email, password_hash, body.department_name),
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()

    token = create_access_token(user_id, username)
    return RegisterResponse(
        access_token=token,
        user_id=user_id,
        name=body.name,
        email=body.email,
        department=body.department_name,
        is_verified=True,
    )


@router.post("/logout")
def logout():
    return {"ok": True}


@router.post("/refresh")
def refresh_token(body: dict):
    """Refresh token - 현재는 새 access token을 재발급 (stateless)"""
    # refresh_token이 없어도 동작하도록 유연하게 처리
    # 실제 구현에서는 DB에서 refresh token 검증 필요
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="재로그인이 필요합니다.")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    if len(body.new_password) < 8:
        raise HTTPException(400, detail="새 비밀번호는 8자 이상이어야 합니다.")
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE id=%s", (uid,))
        user = cursor.fetchone()
        if not user or not verify_password(body.current_password, user["password_hash"]):
            cursor.close()
            raise HTTPException(400, detail="현재 비밀번호가 올바르지 않습니다.")
        new_hash = hash_password(body.new_password)
        cursor.execute("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, uid))
        conn.commit()
        cursor.close()
    return {"ok": True}
