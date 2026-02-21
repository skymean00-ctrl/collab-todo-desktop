import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.user import User, Department, EmailVerificationToken, PasswordResetToken
from app.utils.auth import hash_password, verify_password, create_access_token, get_current_user
from app.utils.email import send_verification_email, send_password_reset
from app.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


# ── Schemas ──────────────────────────────────────────────
DEPARTMENTS = ["현장소장", "공무팀", "공사팀", "안전팀", "품질팀", "직영팀"]

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

    def validate_department(self):
        if self.department_name not in DEPARTMENTS:
            raise ValueError(f"올바르지 않은 부서입니다.")


class TokenResponse(BaseModel):
    access_token: str
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
    # 기존 미사용 토큰 제거
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


def _build_response(user: User, db: Session) -> TokenResponse:
    access_token = create_access_token({"sub": user.id})
    dept_name = user.department.name if user.department else ""
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        department=dept_name,
        job_title=user.job_title or "",
        is_admin=user.is_admin,
        is_verified=user.is_verified,
    )


# ── Endpoints ─────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    req: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if req.department_name not in DEPARTMENTS:
        raise HTTPException(status_code=400, detail="올바르지 않은 부서입니다.")

    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

    # 부서 조회 또는 생성
    dept = db.query(Department).filter(Department.name == req.department_name).first()
    if not dept:
        dept = Department(name=req.department_name)
        db.add(dept)
        db.flush()

    # 첫 번째 가입자는 자동으로 관리자 권한 부여
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

    # 이메일 인증 토큰 생성
    raw_token = _make_verification_token(db, user.id)
    db.commit()
    db.refresh(user)

    # 인증 메일 백그라운드 발송
    verify_url = f"{settings.app_base_url}/#/verify-email/{raw_token}"
    background_tasks.add_task(send_verification_email, user.email, user.name, verify_url)

    # 가입 즉시 로그인 토큰 반환 (자동 로그인)
    return _build_response(user, db)


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username, User.is_active == True).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    return _build_response(user, db)


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
    if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
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
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="새 비밀번호는 6자 이상이어야 합니다.")
    current_user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "비밀번호가 변경되었습니다."}


@router.post("/forgot-password")
async def forgot_password(
    req: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # 보안: 이메일 존재 여부와 무관하게 동일한 응답 반환
    user = db.query(User).filter(User.email == req.email, User.is_active == True).first()
    if user:
        # 기존 미사용 토큰 제거
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
    if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="재설정 링크가 만료되었습니다. 다시 요청해주세요.")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="비밀번호는 6자 이상이어야 합니다.")

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
