from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User, Department, UserNotificationPreference, FilterPreset
from app.utils.auth import get_current_user
from datetime import date

router = APIRouter(prefix="/api/users", tags=["users"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    department_name: Optional[str] = None


class NotificationPrefUpdate(BaseModel):
    notify_assigned: Optional[bool] = None
    notify_status_changed: Optional[bool] = None
    notify_due_soon: Optional[bool] = None
    notify_mentioned: Optional[bool] = None
    notify_reassigned: Optional[bool] = None
    notify_commented: Optional[bool] = None
    email_assigned: Optional[bool] = None
    email_status_changed: Optional[bool] = None
    email_due_soon: Optional[bool] = None
    email_mentioned: Optional[bool] = None
    email_reassigned: Optional[bool] = None


class FilterPresetCreate(BaseModel):
    name: str
    section: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    sort_by: Optional[str] = None
    sort_dir: Optional[str] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None


@router.get("/departments/list")
def departments_list(db: Session = Depends(get_db)):
    """인증 없이 가입 화면에서 사용하는 부서 목록 (DB 기반)"""
    depts = db.query(Department).order_by(Department.name).all()
    return [d.name for d in depts]


@router.get("/departments")
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    depts = db.query(Department).order_by(Department.name).all()
    return [{"id": d.id, "name": d.name} for d in depts]


@router.get("/me/notification-preferences")
def get_notification_prefs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == current_user.id
    ).first()
    if not pref:
        pref = UserNotificationPreference(user_id=current_user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return {
        "notify_assigned": pref.notify_assigned,
        "notify_status_changed": pref.notify_status_changed,
        "notify_due_soon": pref.notify_due_soon,
        "notify_mentioned": pref.notify_mentioned,
        "notify_reassigned": pref.notify_reassigned,
        "notify_commented": pref.notify_commented,
        "email_assigned": pref.email_assigned,
        "email_status_changed": pref.email_status_changed,
        "email_due_soon": pref.email_due_soon,
        "email_mentioned": pref.email_mentioned,
        "email_reassigned": pref.email_reassigned,
    }


@router.patch("/me/notification-preferences")
def update_notification_prefs(
    req: NotificationPrefUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == current_user.id
    ).first()
    if not pref:
        pref = UserNotificationPreference(user_id=current_user.id)
        db.add(pref)
        db.flush()

    for field, val in req.model_dump(exclude_none=True).items():
        setattr(pref, field, val)

    db.commit()
    return {"message": "알림 설정이 저장되었습니다."}


@router.get("/me/filter-presets")
def list_filter_presets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    presets = (
        db.query(FilterPreset)
        .filter(FilterPreset.user_id == current_user.id)
        .order_by(FilterPreset.created_at.asc())
        .all()
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "section": p.section,
            "status": p.status,
            "priority": p.priority,
            "sort_by": p.sort_by,
            "sort_dir": p.sort_dir,
            "due_date_from": p.due_date_from.isoformat() if p.due_date_from else None,
            "due_date_to": p.due_date_to.isoformat() if p.due_date_to else None,
        }
        for p in presets
    ]


@router.post("/me/filter-presets", status_code=201)
def create_filter_preset(
    req: FilterPresetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = db.query(FilterPreset).filter(FilterPreset.user_id == current_user.id).count()
    if count >= 10:
        raise HTTPException(status_code=400, detail="필터 프리셋은 최대 10개까지 저장할 수 있습니다.")
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="프리셋 이름을 입력해주세요.")
    preset = FilterPreset(
        user_id=current_user.id,
        name=req.name.strip(),
        section=req.section,
        status=req.status,
        priority=req.priority,
        sort_by=req.sort_by,
        sort_dir=req.sort_dir,
        due_date_from=req.due_date_from,
        due_date_to=req.due_date_to,
    )
    db.add(preset)
    db.commit()
    return {"id": preset.id, "name": preset.name, "message": "프리셋이 저장되었습니다."}


@router.delete("/me/filter-presets/{preset_id}", status_code=204)
def delete_filter_preset(
    preset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preset = db.query(FilterPreset).filter(
        FilterPreset.id == preset_id,
        FilterPreset.user_id == current_user.id,
    ).first()
    if not preset:
        raise HTTPException(status_code=404, detail="프리셋을 찾을 수 없습니다.")
    db.delete(preset)
    db.commit()


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


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "department": user.department.name if user.department else "",
        "job_title": user.job_title or "",
    }


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
        dept_name = req.department_name.strip()
        if not dept_name:
            raise HTTPException(status_code=400, detail="부서를 입력해주세요.")
        dept = db.query(Department).filter(Department.name == dept_name).first()
        if not dept:
            raise HTTPException(status_code=400, detail="존재하지 않는 부서입니다. 관리자에게 부서 추가를 요청하세요.")
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
