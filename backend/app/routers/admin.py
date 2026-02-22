import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User, Department, SystemSettings
from app.models.task import Task, Notification, StatusEnum
from app.utils.auth import get_current_user, hash_password, validate_password_strength
from app.models.user import PasswordResetToken

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    return current_user


class AnnouncementRequest(BaseModel):
    message: str
    task_id: Optional[int] = None


class BulkReassignRequest(BaseModel):
    from_user_id: int
    to_user_id: int
    task_ids: Optional[List[int]] = None  # None이면 from_user_id의 모든 활성 업무


class DepartmentCreate(BaseModel):
    name: str


class DepartmentUpdate(BaseModel):
    name: str


class SystemSettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None


# ── 사용자 관리 ────────────────────────────────────────────
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
def deactivate_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="자기 자신은 비활성화할 수 없습니다.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True, User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="마지막 관리자는 비활성화할 수 없습니다.")
    user.is_active = False
    db.commit()
    return {"message": f"{user.name} 계정이 비활성화되었습니다."}


@router.patch("/users/{user_id}/activate")
def activate_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if user.is_active:
        raise HTTPException(status_code=400, detail="이미 활성화된 계정입니다.")
    user.is_active = True
    db.commit()
    return {"message": f"{user.name} 계정이 활성화되었습니다."}


@router.patch("/users/{user_id}/toggle-admin")
def toggle_admin(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="자신의 관리자 권한은 변경할 수 없습니다.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if user.is_admin:
        admin_count = db.query(User).filter(User.is_admin == True, User.is_active == True).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="마지막 관리자의 권한은 해제할 수 없습니다.")
    user.is_admin = not user.is_admin
    db.commit()
    action = "부여" if user.is_admin else "해제"
    return {"message": f"{user.name}의 관리자 권한이 {action}되었습니다.", "is_admin": user.is_admin}


@router.post("/users/{user_id}/reset-password")
def force_reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """관리자가 사용자 비밀번호를 임시값으로 강제 초기화"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 임시 비밀번호 생성 (12자: 대소문자 + 숫자 + 특수문자 포함)
    temp_pw = secrets.token_urlsafe(8) + "A1!"
    user.password_hash = hash_password(temp_pw)
    db.commit()
    return {
        "message": f"{user.name}의 비밀번호가 임시 비밀번호로 초기화되었습니다.",
        "temp_password": temp_pw,
    }


# ── 부서 관리 ──────────────────────────────────────────────
@router.get("/departments")
def list_departments(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    depts = db.query(Department).order_by(Department.name).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "user_count": len([u for u in d.users if u.is_active]),
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in depts
    ]


@router.post("/departments", status_code=201)
def create_department(
    req: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="부서명을 입력해주세요.")
    if db.query(Department).filter(Department.name == name).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 부서입니다.")
    dept = Department(name=name)
    db.add(dept)
    db.commit()
    return {"id": dept.id, "name": dept.name, "message": "부서가 생성되었습니다."}


@router.patch("/departments/{dept_id}")
def update_department(
    dept_id: int,
    req: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="부서명을 입력해주세요.")
    existing = db.query(Department).filter(Department.name == name, Department.id != dept_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 부서명입니다.")
    dept.name = name
    db.commit()
    return {"id": dept.id, "name": dept.name, "message": "부서명이 수정되었습니다."}


@router.delete("/departments/{dept_id}", status_code=204)
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    user_count = db.query(User).filter(User.department_id == dept_id, User.is_active == True).count()
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"해당 부서에 활성 사용자 {user_count}명이 있습니다. 먼저 사용자를 다른 부서로 이동해주세요.",
        )
    db.delete(dept)
    db.commit()


# ── 전체 통계 대시보드 ─────────────────────────────────────
@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """관리자용 전체 업무 통계"""
    from datetime import date

    today = date.today()

    total_users = db.query(User).filter(User.is_active == True).count()
    total_tasks = db.query(Task).filter(Task.is_subtask == False).count()

    # 상태별
    status_breakdown = {}
    for s in StatusEnum:
        count = db.query(Task).filter(Task.status == s, Task.is_subtask == False).count()
        status_breakdown[s.value] = count

    # 우선순위별
    from app.models.task import PriorityEnum
    priority_breakdown = {}
    for p in PriorityEnum:
        count = db.query(Task).filter(Task.priority == p, Task.is_subtask == False).count()
        priority_breakdown[p.value] = count

    # 마감 초과
    overdue = db.query(Task).filter(
        Task.due_date < today,
        Task.status.notin_([StatusEnum.approved]),
        Task.is_subtask == False,
    ).count()

    # 부서별 업무 수 (담당자 기준)
    dept_stats = []
    depts = db.query(Department).all()
    for dept in depts:
        user_ids = [u.id for u in dept.users if u.is_active]
        if not user_ids:
            continue
        count = db.query(Task).filter(
            Task.assignee_id.in_(user_ids),
            Task.is_subtask == False,
        ).count()
        dept_stats.append({"department": dept.name, "task_count": count})

    # 사용자별 미완료 업무 TOP 10
    from sqlalchemy import desc
    user_task_counts = (
        db.query(User.id, User.name, func.count(Task.id).label("cnt"))
        .join(Task, Task.assignee_id == User.id)
        .filter(
            User.is_active == True,
            Task.status.notin_([StatusEnum.approved]),
            Task.is_subtask == False,
        )
        .group_by(User.id, User.name)
        .order_by(desc("cnt"))
        .limit(10)
        .all()
    )

    return {
        "total_users": total_users,
        "total_tasks": total_tasks,
        "overdue": overdue,
        "status_breakdown": status_breakdown,
        "priority_breakdown": priority_breakdown,
        "dept_stats": dept_stats,
        "top_assignees": [
            {"user_id": r.id, "name": r.name, "pending_tasks": r.cnt}
            for r in user_task_counts
        ],
    }


# ── 업무 이관 ─────────────────────────────────────────────
@router.post("/tasks/bulk-reassign")
def bulk_reassign_tasks(
    req: BulkReassignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """특정 사용자의 업무를 다른 사용자에게 일괄 이관"""
    from app.models.task import TaskLog

    from_user = db.query(User).filter(User.id == req.from_user_id).first()
    to_user = db.query(User).filter(User.id == req.to_user_id, User.is_active == True).first()
    if not from_user:
        raise HTTPException(status_code=404, detail="이관 출발 사용자를 찾을 수 없습니다.")
    if not to_user:
        raise HTTPException(status_code=404, detail="이관 대상 사용자를 찾을 수 없습니다.")
    if req.from_user_id == req.to_user_id:
        raise HTTPException(status_code=400, detail="같은 사용자로는 이관할 수 없습니다.")

    query = db.query(Task).filter(
        Task.assignee_id == req.from_user_id,
        Task.status.notin_([StatusEnum.approved]),
    )
    if req.task_ids:
        query = query.filter(Task.id.in_(req.task_ids))

    tasks = query.all()
    if not tasks:
        raise HTTPException(status_code=404, detail="이관할 업무가 없습니다.")

    for task in tasks:
        task.assignee_id = req.to_user_id
        db.add(TaskLog(
            task_id=task.id,
            user_id=current_user.id,
            action="reassigned",
            old_value=from_user.name,
            new_value=to_user.name,
            comment=f"관리자에 의한 일괄 이관: {from_user.name} → {to_user.name}",
        ))
        # 이관 알림
        db.add(Notification(
            user_id=req.to_user_id,
            task_id=task.id,
            type="reassigned",
            message=f"업무가 이관되었습니다: {task.title}",
        ))

    db.commit()
    return {
        "message": f"{len(tasks)}개 업무가 {from_user.name} → {to_user.name}으로 이관되었습니다.",
        "count": len(tasks),
    }


# ── 공지 알림 발송 ─────────────────────────────────────────
@router.post("/announcements")
def send_announcement(
    req: AnnouncementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """전체 활성 사용자에게 공지 알림 발송"""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="공지 내용을 입력해주세요.")

    users = db.query(User).filter(User.is_active == True, User.id != current_user.id).all()
    if not users:
        raise HTTPException(status_code=400, detail="발송할 사용자가 없습니다.")

    for user in users:
        db.add(Notification(
            user_id=user.id,
            task_id=req.task_id,
            type="announcement",
            message=f"[공지] {req.message.strip()}",
        ))

    db.commit()
    return {"message": f"{len(users)}명에게 공지가 발송되었습니다."}


# ── 시스템 설정 ────────────────────────────────────────────
@router.get("/settings")
def list_settings(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    settings = db.query(SystemSettings).all()
    return [
        {"key": s.key, "value": s.value, "description": s.description, "updated_at": s.updated_at}
        for s in settings
    ]


@router.put("/settings/{key}")
def upsert_setting(
    key: str,
    req: SystemSettingUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if setting:
        setting.value = req.value
        if req.description is not None:
            setting.description = req.description
    else:
        setting = SystemSettings(key=key, value=req.value, description=req.description)
        db.add(setting)
    db.commit()
    return {"key": setting.key, "value": setting.value, "message": "설정이 저장되었습니다."}
