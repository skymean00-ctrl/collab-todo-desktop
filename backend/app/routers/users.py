from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Department
from app.utils.auth import get_current_user
from app.routers.auth import DEPARTMENTS

router = APIRouter(prefix="/api/users", tags=["users"])


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
