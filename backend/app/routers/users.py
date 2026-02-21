from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User, Department
from app.utils.auth import get_current_user
from app.routers.auth import DEPARTMENTS

router = APIRouter(prefix="/api/users", tags=["users"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    department_name: Optional[str] = None


@router.get("/")
def list_users(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    users = db.query(User).filter(User.is_active == True).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "department": u.department.name if u.department else "",
            "job_title": u.job_title,
        }
        for u in users
    ]


@router.get("/departments")
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    depts = db.query(Department).all()
    return [{"id": d.id, "name": d.name} for d in depts]


@router.get("/departments/list")
def departments_list():
    """인증 없이 가입 화면에서 사용하는 부서 목록"""
    return DEPARTMENTS


@router.patch("/me")
def update_my_profile(
    req: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.name is not None:
        if not req.name.strip():
            raise HTTPException(status_code=400, detail="이름을 입력해주세요.")
        current_user.name = req.name.strip()
    if req.job_title is not None:
        current_user.job_title = req.job_title.strip() or None
    if req.department_name is not None:
        if req.department_name not in DEPARTMENTS:
            raise HTTPException(status_code=400, detail="올바르지 않은 부서입니다.")
        dept = db.query(Department).filter(Department.name == req.department_name).first()
        if not dept:
            dept = Department(name=req.department_name)
            db.add(dept)
            db.flush()
        current_user.department_id = dept.id
    db.commit()
    db.refresh(current_user)
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "department": current_user.department.name if current_user.department else "",
        "job_title": current_user.job_title or "",
        "is_admin": current_user.is_admin,
        "is_verified": current_user.is_verified,
    }
