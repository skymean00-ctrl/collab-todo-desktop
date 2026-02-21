from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional, List
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.task import Task, TaskLog, Notification, Category, Tag, StatusEnum, PriorityEnum
from app.utils.auth import get_current_user
from app.utils.email import send_task_assigned, send_status_changed
import asyncio

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ── Schemas ──────────────────────────────────────────────
class MaterialProvider(BaseModel):
    """지시자가 직접 지정하는 자료제공자"""
    assignee_id: int
    title: str
    due_date: Optional[date] = None


class TaskCreate(BaseModel):
    title: str
    content: Optional[str] = None
    assignee_id: int                          # 주 담당자
    category_id: Optional[int] = None
    priority: PriorityEnum = PriorityEnum.normal
    estimated_hours: Optional[float] = None
    due_date: Optional[date] = None
    tag_names: List[str] = []
    parent_task_id: Optional[int] = None
    is_subtask: bool = False
    # 흐름2: 지시자가 직접 자료제공자를 지정 (주담당자와 동시에 배정)
    material_providers: List[MaterialProvider] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    priority: Optional[PriorityEnum] = None
    estimated_hours: Optional[float] = None
    due_date: Optional[date] = None
    progress: Optional[int] = None
    tag_names: Optional[List[str]] = None


class StatusChange(BaseModel):
    status: StatusEnum
    comment: Optional[str] = None


# ── Helpers ──────────────────────────────────────────────
def task_to_dict(t: Task) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "content": t.content,
        "assigner": {"id": t.assigner.id, "name": t.assigner.name} if t.assigner else None,
        "assignee": {"id": t.assignee.id, "name": t.assignee.name} if t.assignee else None,
        "category": {"id": t.category.id, "name": t.category.name, "color": t.category.color} if t.category else None,
        "priority": t.priority,
        "status": t.status,
        "progress": t.progress,
        "estimated_hours": float(t.estimated_hours) if t.estimated_hours else None,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "is_subtask": t.is_subtask,
        "parent_task_id": t.parent_task_id,
        "tags": [{"id": tag.id, "name": tag.name} for tag in t.tags],
        "attachment_count": len(t.attachments),
        "subtask_count": len(t.subtasks),
        "subtasks_done": sum(1 for s in t.subtasks if s.status == StatusEnum.approved),
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _get_or_create_tags(db: Session, names: List[str]) -> List[Tag]:
    tags = []
    for name in names:
        name = name.strip()
        if not name:
            continue
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


def _add_notification(db: Session, user_id: int, task_id: int, ntype: str, message: str):
    notif = Notification(user_id=user_id, task_id=task_id, type=ntype, message=message)
    db.add(notif)


# ── Endpoints ─────────────────────────────────────────────
@router.post("/", status_code=201)
async def create_task(req: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assignee = db.query(User).filter(User.id == req.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="담당자를 찾을 수 없습니다.")

    task = Task(
        title=req.title,
        content=req.content,
        assigner_id=current_user.id,
        assignee_id=req.assignee_id,
        category_id=req.category_id,
        priority=req.priority,
        estimated_hours=req.estimated_hours,
        due_date=req.due_date,
        parent_task_id=req.parent_task_id,
        is_subtask=req.is_subtask,
    )
    task.tags = _get_or_create_tags(db, req.tag_names)
    db.add(task)
    db.flush()

    # 로그
    db.add(TaskLog(task_id=task.id, user_id=current_user.id, action="created", new_value="pending"))
    # 주 담당자 알림
    _add_notification(db, assignee.id, task.id, "assigned", f"새 업무가 배정되었습니다: {task.title}")

    # 흐름2: 지시자가 직접 자료제공자를 서브태스크로 동시 생성
    material_assignees = []
    for mp in req.material_providers:
        provider = db.query(User).filter(User.id == mp.assignee_id).first()
        if not provider:
            continue
        subtask = Task(
            title=mp.title,
            content=f"[자료제공] {task.title} 업무의 자료 제공 요청",
            assigner_id=current_user.id,
            assignee_id=mp.assignee_id,
            priority=req.priority,
            due_date=mp.due_date or req.due_date,
            parent_task_id=task.id,
            is_subtask=True,
        )
        db.add(subtask)
        db.flush()
        db.add(TaskLog(task_id=subtask.id, user_id=current_user.id, action="created", new_value="pending"))
        _add_notification(db, mp.assignee_id, subtask.id, "assigned", f"자료 제공 요청: {mp.title}")
        material_assignees.append((provider, subtask))

    db.commit()

    # 이메일 (비동기, 실패해도 API는 성공)
    try:
        await send_task_assigned(
            to=assignee.email,
            assignee_name=assignee.name,
            task_title=task.title,
            assigner_name=current_user.name,
            due_date=str(req.due_date) if req.due_date else "미정",
        )
    except Exception:
        pass

    for provider, subtask in material_assignees:
        try:
            await send_task_assigned(
                to=provider.email,
                assignee_name=provider.name,
                task_title=subtask.title,
                assigner_name=current_user.name,
                due_date=str(subtask.due_date) if subtask.due_date else "미정",
            )
        except Exception:
            pass

    return task_to_dict(db.query(Task).options(
        joinedload(Task.assigner), joinedload(Task.assignee),
        joinedload(Task.category), joinedload(Task.tags),
        joinedload(Task.attachments), joinedload(Task.subtasks),
    ).filter(Task.id == task.id).first())


@router.get("/")
def list_tasks(
    section: Optional[str] = Query(None),  # assigned_to_me, assigned_by_me, subtasks_to_me
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Task).options(
        joinedload(Task.assigner), joinedload(Task.assignee),
        joinedload(Task.category), joinedload(Task.tags),
        joinedload(Task.attachments), joinedload(Task.subtasks),
    )

    if section == "assigned_to_me":
        q = q.filter(Task.assignee_id == current_user.id, Task.is_subtask == False)
    elif section == "assigned_by_me":
        q = q.filter(Task.assigner_id == current_user.id, Task.is_subtask == False)
    elif section == "subtasks_to_me":
        q = q.filter(Task.assignee_id == current_user.id, Task.is_subtask == True)

    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == priority)
    if assignee_id:
        q = q.filter(Task.assignee_id == assignee_id)
    if search:
        q = q.filter(or_(Task.title.contains(search), Task.content.contains(search)))

    tasks = q.order_by(Task.created_at.desc()).all()
    return [task_to_dict(t) for t in tasks]


@router.get("/dashboard")
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import date, timedelta
    today = date.today()
    in_3_days = today + timedelta(days=3)

    my_tasks = db.query(Task).filter(Task.assignee_id == current_user.id, Task.is_subtask == False)

    total = my_tasks.count()
    urgent = my_tasks.filter(Task.priority == PriorityEnum.urgent, Task.status != StatusEnum.approved).count()
    due_soon = my_tasks.filter(
        Task.due_date <= in_3_days,
        Task.due_date >= today,
        Task.status.notin_([StatusEnum.approved]),
    ).count()
    rejected = my_tasks.filter(Task.status == StatusEnum.rejected).count()

    return {"total": total, "urgent": urgent, "due_soon": due_soon, "rejected": rejected}


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    task = db.query(Task).options(
        joinedload(Task.assigner), joinedload(Task.assignee),
        joinedload(Task.category), joinedload(Task.tags),
        joinedload(Task.attachments), joinedload(Task.subtasks),
        joinedload(Task.logs),
    ).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="업무를 찾을 수 없습니다.")
    return task_to_dict(task)


@router.patch("/{task_id}")
def update_task(task_id: int, req: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="업무를 찾을 수 없습니다.")
    if current_user.id not in (task.assigner_id, task.assignee_id) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="업무를 수정할 권한이 없습니다.")

    if req.title is not None:
        task.title = req.title
    if req.content is not None:
        task.content = req.content
    if req.category_id is not None:
        task.category_id = req.category_id
    if req.priority is not None:
        task.priority = req.priority
    if req.estimated_hours is not None:
        task.estimated_hours = req.estimated_hours
    if req.due_date is not None:
        task.due_date = req.due_date
    if req.progress is not None:
        task.progress = max(0, min(100, req.progress))
    if req.tag_names is not None:
        task.tags = _get_or_create_tags(db, req.tag_names)

    db.add(TaskLog(task_id=task.id, user_id=current_user.id, action="updated"))
    db.commit()
    return {"message": "업무가 수정되었습니다."}


@router.post("/{task_id}/status")
async def change_status(
    task_id: int, req: StatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).options(
        joinedload(Task.assigner), joinedload(Task.assignee)
    ).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="업무를 찾을 수 없습니다.")
    if current_user.id not in (task.assigner_id, task.assignee_id) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="상태를 변경할 권한이 없습니다.")

    old_status = task.status
    task.status = req.status

    db.add(TaskLog(
        task_id=task.id,
        user_id=current_user.id,
        action="status_changed",
        old_value=old_status,
        new_value=req.status,
        comment=req.comment,
    ))

    # 알림 대상 결정
    notify_user_id = task.assigner_id if current_user.id == task.assignee_id else task.assignee_id
    _add_notification(db, notify_user_id, task.id, "status_changed", f"업무 상태 변경: {task.title} → {req.status}")

    db.commit()

    # 이메일
    notify_user = db.query(User).filter(User.id == notify_user_id).first()
    try:
        await send_status_changed(
            to=notify_user.email,
            user_name=notify_user.name,
            task_title=task.title,
            old_status=old_status,
            new_status=req.status,
        )
    except Exception:
        pass

    return {"message": "상태가 변경되었습니다."}


@router.get("/{task_id}/logs")
def get_logs(task_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    logs = db.query(TaskLog).filter(TaskLog.task_id == task_id).order_by(TaskLog.created_at.asc()).all()
    return [
        {
            "id": l.id,
            "user": {"id": l.user.id, "name": l.user.name} if l.user else None,
            "action": l.action,
            "old_value": l.old_value,
            "new_value": l.new_value,
            "comment": l.comment,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
