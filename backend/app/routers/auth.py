import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.user import User, Department, EmailVerificationToken, PasswordResetToken, RefreshToken
from app.utils.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, validate_password_strength, create_refresh_token_value,
)
from app.utils.email import send_verification_email, send_password_reset
from app.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()

# Refresh token 유효기간 (7일)
_REFRESH_EXPIRE_DAYS = 7


# ── Schemas ──────────────────────────────────────────────
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    department_name: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str
    department: str
    job_title: str
    is_admin: bool
    is_verified: bool


# ── Helpers ───────────────────────────────────────────────
def _make_verification_token(db: Session, user_id: int) -> str:
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user_id,
        EmailVerificationToken.used == False,
    ).delete()

    raw = secrets.token_urlsafe(32)
    token = EmailVerificationToken(
        user_id=user_id,
        token=raw,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(token)
    db.flush()
    return raw


def _make_refresh_token(db: Session, user_id: int) -> str:
    """새 Refresh Token 생성 후 DB 저장. 기존 만료 토큰 정리."""
    # 기존 만료 토큰 정리 (최대 5개 유지)
    old_tokens = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
        .order_by(RefreshToken.created_at.asc())
        .all()
    )
    if len(old_tokens) >= 5:
        for t in old_tokens[:-4]:
            t.revoked = True

    raw = create_refresh_token_value()
    rt = RefreshToken(
        user_id=user_id,
        token=raw,
        expires_at=datetime.now(timezone.utc) + timedelta(days=_REFRESH_EXPIRE_DAYS),
    )
    db.add(rt)
    db.flush()
    return raw


def _build_response(user: User, db: Session) -> TokenResponse:
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = _make_refresh_token(db, user.id)
    db.commit()
    dept_name = user.department.name if user.department else ""
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        department=dept_name,
        job_title=user.job_title or "",
        is_admin=user.is_admin,
        is_verified=user.is_verified,
    )


def _get_departments(db: Session) -> list[str]:
    """DB에서 부서 목록 조회"""
    return [d.name for d in db.query(Department).order_by(Department.name).all()]


# ── Endpoints ─────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    req: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

    # 비밀번호 복잡도 검증
    try:
        validate_password_strength(req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 부서명 유효성: DB에 없으면 생성 (관리자가 DB에서 관리)
    dept_name = req.department_name.strip()
    if not dept_name:
        raise HTTPException(status_code=400, detail="부서를 선택해주세요.")

    dept = db.query(Department).filter(Department.name == dept_name).first()
    if not dept:
        dept = Department(name=dept_name)
        db.add(dept)
        db.flush()

    is_first_user = db.query(User).count() == 0

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        name=req.name,
        department_id=dept.id,
        job_title=None,
        is_admin=is_first_user,
        is_verified=False,
    )
    db.add(user)
    db.flush()

    raw_token = _make_verification_token(db, user.id)
    db.commit()
    db.refresh(user)

    verify_url = f"{settings.app_base_url}/#/verify-email/{raw_token}"
    background_tasks.add_task(send_verification_email, user.email, user.name, verify_url)

    return _build_response(user, db)


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username, User.is_active == True).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    return _build_response(user, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh Token으로 새 Access Token + Refresh Token 발급"""
    now = datetime.now(timezone.utc)
    record = db.query(RefreshToken).filter(
        RefreshToken.token == req.refresh_token,
        RefreshToken.revoked == False,
    ).first()

    if not record:
        raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token입니다.")

    expires = record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        record.revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh Token이 만료되었습니다. 다시 로그인해주세요.")

    user = db.query(User).filter(User.id == record.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="계정을 찾을 수 없습니다.")

    # 기존 토큰 폐기 (rotation)
    record.revoked = True
    db.flush()

    return _build_response(user, db)


@router.post("/logout")
def logout(req: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh Token 폐기"""
    record = db.query(RefreshToken).filter(RefreshToken.token == req.refresh_token).first()
    if record:
        record.revoked = True
        db.commit()
    return {"message": "로그아웃되었습니다."}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "department": current_user.department.name if current_user.department else "",
        "job_title": current_user.job_title,
        "is_admin": current_user.is_admin,
        "is_verified": current_user.is_verified,
    }


@router.post("/verify-email/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    record = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == token,
        EmailVerificationToken.used == False,
    ).first()

    if not record:
        raise HTTPException(status_code=400, detail="유효하지 않은 인증 링크입니다.")
    expires = record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="인증 링크가 만료되었습니다. 재발송을 요청해주세요.")

    record.used = True
    record.user.is_verified = True
    db.commit()
    return {"message": "이메일 인증이 완료되었습니다."}


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
    try:
        validate_password_strength(req.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    current_user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "비밀번호가 변경되었습니다."}


@router.post("/forgot-password")
async def forgot_password(
    req: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == req.email, User.is_active == True).first()
    if user:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
        ).delete()

        raw = secrets.token_urlsafe(32)
        token = PasswordResetToken(
            user_id=user.id,
            token=raw,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(token)
        db.commit()

        reset_url = f"{settings.app_base_url}/#/reset-password/{raw}"
        background_tasks.add_task(send_password_reset, user.email, user.name, reset_url)

    return {"message": "입력한 이메일로 재설정 링크를 발송했습니다. (계정이 존재하는 경우)"}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == req.token,
        PasswordResetToken.used == False,
    ).first()

    if not record:
        raise HTTPException(status_code=400, detail="유효하지 않은 재설정 링크입니다.")
    expires = record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="재설정 링크가 만료되었습니다. 다시 요청해주세요.")

    try:
        validate_password_strength(req.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    record.used = True
    record.user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "비밀번호가 재설정되었습니다. 새 비밀번호로 로그인해주세요."}


@router.post("/resend-verification")
async def resend_verification(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_verified:
        raise HTTPException(status_code=400, detail="이미 인증된 계정입니다.")

    raw_token = _make_verification_token(db, current_user.id)
    db.commit()

    verify_url = f"{settings.app_base_url}/#/verify-email/{raw_token}"
    background_tasks.add_task(send_verification_email, current_user.email, current_user.name, verify_url)
    return {"message": "인증 메일을 재발송했습니다."}
