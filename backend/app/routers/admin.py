from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    return current_user


@router.get("/users")
def list_all_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.query(User).order_by(User.created_at.asc()).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "department": u.department.name if u.department else "",
            "job_title": u.job_title,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "is_verified": u.is_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="자기 자신은 삭제할 수 없습니다.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 마지막 관리자 비활성화 방지
    if user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True, User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="마지막 관리자는 비활성화할 수 없습니다.")

    # 완전 삭제 대신 비활성화 (업무 이력 보존)
    user.is_active = False
    db.commit()
    return {"message": f"{user.name} 계정이 비활성화되었습니다."}


@router.patch("/users/{user_id}/toggle-admin")
def toggle_admin(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="자신의 관리자 권한은 변경할 수 없습니다.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 마지막 관리자 권한 해제 방지
    if user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True, User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="마지막 관리자의 권한은 해제할 수 없습니다.")

    user.is_admin = not user.is_admin
    db.commit()
    action = "부여" if user.is_admin else "해제"
    return {"message": f"{user.name}의 관리자 권한이 {action}되었습니다.", "is_admin": user.is_admin}
