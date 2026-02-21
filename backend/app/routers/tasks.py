import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, case
from typing import Optional, List
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.task import Task, TaskLog, Notification, Category, Tag, StatusEnum, PriorityEnum, task_tags
from app.utils.auth import get_current_user
from app.utils.email import send_task_assigned, send_status_changed
from app.config import get_settings
import asyncio

_settings = get_settings()

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# ── 검색 키워드 → 필터 매핑 ────────────────────────────────
# 사용자가 "반려" "긴급" 등을 검색창에 입력하면 해당 필터로 자동 전환
SEARCH_STATUS_KEYWORDS: dict[str, StatusEnum] = {
    "대기": StatusEnum.pending,
    "진행중": StatusEnum.in_progress,
    "진행": StatusEnum.in_progress,
    "검토": StatusEnum.review,
    "검토요청": StatusEnum.review,
    "검토중": StatusEnum.review,
    "완료": StatusEnum.approved,
    "승인": StatusEnum.approved,
    "반려": StatusEnum.rejected,
    "반려됨": StatusEnum.rejected,
}

SEARCH_PRIORITY_KEYWORDS: dict[str, PriorityEnum] = {
    "긴급": PriorityEnum.urgent,
    "급함": PriorityEnum.urgent,
    "급한": PriorityEnum.urgent,
    "높음": PriorityEnum.high,
    "보통": PriorityEnum.normal,
    "낮음": PriorityEnum.low,
}


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
    assignee_id: Optional[int] = None
    category_id: Optional[int] = None
    priority: Optional[PriorityEnum] = None
    estimated_hours: Optional[float] = None
    due_date: Optional[date] = None
    progress: Optional[int] = None
    tag_names: Optional[List[str]] = None


class CommentRequest(BaseModel):
    comment: str


class CommentUpdate(BaseModel):
    comment: str


class StatusChange(BaseModel):
    status: StatusEnum
    comment: Optional[str] = None


class BulkStatusChange(BaseModel):
    task_ids: List[int]
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
    section: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    due_date_from: Optional[date] = Query(None),
    due_date_to: Optional[date] = Query(None),
    sort_by: Optional[str] = Query(None),   # created_at | due_date | priority | status | title
    sort_dir: str = Query("desc"),           # asc | desc
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ── 검색어 파싱 ──────────────────────────────────────────
    # 스페이스로 분리 → 각 단어를 상태/우선순위 키워드 또는 텍스트 검색어로 분류
    text_terms: List[str] = []
    implied_status: Optional[StatusEnum] = None
    implied_priority: Optional[PriorityEnum] = None

    if search:
        for word in search.strip().split():
            if word in SEARCH_STATUS_KEYWORDS and status is None and implied_status is None:
                implied_status = SEARCH_STATUS_KEYWORDS[word]
            elif word in SEARCH_PRIORITY_KEYWORDS and priority is None and implied_priority is None:
                implied_priority = SEARCH_PRIORITY_KEYWORDS[word]
            else:
                text_terms.append(word)

    def apply_filters(q):
        if section == "assigned_to_me":
            q = q.filter(Task.assignee_id == current_user.id, Task.is_subtask == False)
        elif section == "assigned_by_me":
            q = q.filter(Task.assigner_id == current_user.id, Task.is_subtask == False)
        elif section == "subtasks_to_me":
            q = q.filter(Task.assignee_id == current_user.id, Task.is_subtask == True)

        if status:
            q = q.filter(Task.status == status)
        elif implied_status:
            q = q.filter(Task.status == implied_status)

        if priority:
            q = q.filter(Task.priority == priority)
        elif implied_priority:
            q = q.filter(Task.priority == implied_priority)

        if assignee_id:
            q = q.filter(Task.assignee_id == assignee_id)

        # ── 확장 텍스트 검색 ──────────────────────────────────
        # 각 단어를 AND 조건으로 처리, 검색 범위: 제목·내용·담당자명·지시자명·태그명·카테고리명
        for term in text_terms:
            user_ids_matching = db.query(User.id).filter(User.name.contains(term))
            tag_ids_matching = db.query(Tag.id).filter(Tag.name.contains(term))
            cat_ids_matching = db.query(Category.id).filter(Category.name.contains(term))
            task_ids_with_tag = db.query(task_tags.c.task_id).filter(
                task_tags.c.tag_id.in_(tag_ids_matching)
            )
            q = q.filter(or_(
                Task.title.contains(term),
                Task.content.contains(term),
                Task.assignee_id.in_(user_ids_matching),
                Task.assigner_id.in_(user_ids_matching),
                Task.category_id.in_(cat_ids_matching),
                Task.id.in_(task_ids_with_tag),
            ))

        if due_date_from:
            q = q.filter(Task.due_date >= due_date_from)
        if due_date_to:
            q = q.filter(Task.due_date <= due_date_to)
        return q

    # ── 정렬 처리 ────────────────────────────────────────────
    PRIORITY_ORDER = case(
        (Task.priority == PriorityEnum.urgent, 1),
        (Task.priority == PriorityEnum.high, 2),
        (Task.priority == PriorityEnum.normal, 3),
        (Task.priority == PriorityEnum.low, 4),
        else_=5,
    )
    STATUS_ORDER = case(
        (Task.status == StatusEnum.rejected, 1),
        (Task.status == StatusEnum.pending, 2),
        (Task.status == StatusEnum.in_progress, 3),
        (Task.status == StatusEnum.review, 4),
        (Task.status == StatusEnum.approved, 5),
        else_=6,
    )
    asc_flag = sort_dir == "asc"
    # MariaDB는 NULLS LAST/FIRST 문법을 지원하지 않으므로
    # due_date NULL 정렬은 CASE 표현식으로 대체
    DUE_DATE_NULL_FLAG = case((Task.due_date.is_(None), 1), else_=0)
    sort_map = {
        "due_date": (DUE_DATE_NULL_FLAG.asc(), Task.due_date.asc()) if asc_flag else (DUE_DATE_NULL_FLAG.asc(), Task.due_date.desc()),
        "priority": PRIORITY_ORDER.asc() if asc_flag else PRIORITY_ORDER.desc(),
        "status": STATUS_ORDER.asc() if asc_flag else STATUS_ORDER.desc(),
        "title": Task.title.asc() if asc_flag else Task.title.desc(),
        "created_at": Task.created_at.asc() if asc_flag else Task.created_at.desc(),
    }
    order_expr = sort_map.get(sort_by, Task.created_at.desc())
    order_clause = list(order_expr) if isinstance(order_expr, tuple) else [order_expr]

    # joinedload 없이 count → 1:N JOIN 행 중복 방지
    total = apply_filters(db.query(Task)).count()

    items = apply_filters(
        db.query(Task).options(
            joinedload(Task.assigner), joinedload(Task.assignee),
            joinedload(Task.category), joinedload(Task.tags),
            joinedload(Task.attachments), joinedload(Task.subtasks),
        )
    ).order_by(*order_clause).offset((page - 1) * page_size).limit(page_size).all()

    return {"items": [task_to_dict(t) for t in items], "total": total, "page": page, "page_size": page_size}


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

    status_breakdown = {s.value: my_tasks.filter(Task.status == s).count() for s in StatusEnum}

    return {"total": total, "urgent": urgent, "due_soon": due_soon, "rejected": rejected, "status_breakdown": status_breakdown}


@router.post("/bulk-status")
async def bulk_change_status(
    req: BulkStatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.status == StatusEnum.rejected and not req.comment:
        raise HTTPException(status_code=400, detail="반려 시 코멘트는 필수입니다.")
    if not req.task_ids:
        raise HTTPException(status_code=400, detail="업무를 선택해주세요.")

    updated = 0
    for task_id in req.task_ids:
        task = db.query(Task).options(
            joinedload(Task.assigner), joinedload(Task.assignee)
        ).filter(Task.id == task_id).first()
        if not task:
            continue
        if current_user.id not in (task.assigner_id, task.assignee_id) and not current_user.is_admin:
            continue

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
        notify_user_id = task.assigner_id if current_user.id == task.assignee_id else task.assignee_id
        _add_notification(db, notify_user_id, task.id, "status_changed",
                          f"업무 상태 변경: {task.title} → {req.status}")
        updated += 1

    db.commit()
    return {"message": f"{updated}건의 업무 상태가 변경되었습니다.", "updated": updated}


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

    reassigned = False
    if req.assignee_id is not None and current_user.id == task.assigner_id:
        new_assignee = db.query(User).filter(User.id == req.assignee_id, User.is_active == True).first()
        if not new_assignee:
            raise HTTPException(status_code=404, detail="담당자를 찾을 수 없습니다.")
        old_assignee_id = task.assignee_id
        task.assignee_id = req.assignee_id
        db.add(TaskLog(task_id=task.id, user_id=current_user.id, action="reassigned",
                       old_value=str(old_assignee_id), new_value=str(req.assignee_id)))
        _add_notification(db, req.assignee_id, task.id, "assigned", f"업무가 재배정되었습니다: {task.title}")
        reassigned = True

    # Bug fix: 담당자 변경만 한 경우 updated 로그 중복 추가 방지
    other_fields_changed = any(v is not None for v in [
        req.title, req.content, req.category_id, req.priority,
        req.estimated_hours, req.due_date, req.progress, req.tag_names,
    ])
    if other_fields_changed or not reassigned:
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

    if req.status == StatusEnum.rejected and not req.comment:
        raise HTTPException(status_code=400, detail="반려 시 코멘트는 필수입니다.")

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


@router.post("/{task_id}/comment")
def add_comment(
    task_id: int,
    req: CommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="업무를 찾을 수 없습니다.")
    if current_user.id not in (task.assigner_id, task.assignee_id) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="댓글을 작성할 권한이 없습니다.")
    if not req.comment.strip():
        raise HTTPException(status_code=400, detail="댓글 내용을 입력해주세요.")
    db.add(TaskLog(task_id=task.id, user_id=current_user.id, action="comment", comment=req.comment.strip()))
    db.commit()
    return {"message": "댓글이 등록되었습니다."}


@router.post("/{task_id}/clone", status_code=201)
async def clone_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original = db.query(Task).options(joinedload(Task.tags)).filter(Task.id == task_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="업무를 찾을 수 없습니다.")
    if current_user.id not in (original.assigner_id, original.assignee_id) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="업무를 복사할 권한이 없습니다.")

    cloned = Task(
        title=f"[복사] {original.title}",
        content=original.content,
        assigner_id=current_user.id,
        assignee_id=original.assignee_id,
        category_id=original.category_id,
        priority=original.priority,
        estimated_hours=original.estimated_hours,
        due_date=original.due_date,
        is_subtask=original.is_subtask,
        parent_task_id=original.parent_task_id,
    )
    cloned.tags = list(original.tags)
    db.add(cloned)
    db.flush()
    db.add(TaskLog(task_id=cloned.id, user_id=current_user.id, action="created", new_value="pending"))
    _add_notification(db, original.assignee_id, cloned.id, "assigned", f"업무가 복사 배정되었습니다: {cloned.title}")
    db.commit()
    return {"message": "업무가 복사되었습니다.", "task_id": cloned.id}


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).options(
        joinedload(Task.subtasks).joinedload(Task.attachments),
        joinedload(Task.attachments),
    ).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="업무를 찾을 수 없습니다.")
    if current_user.id != task.assigner_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="업무를 삭제할 권한이 없습니다.")

    # 물리 파일 삭제 (attachment 레코드 cascade 전에 처리)
    all_attachments = list(task.attachments)
    for subtask in task.subtasks:
        all_attachments.extend(subtask.attachments)
    for att in all_attachments:
        fpath = os.path.join(_settings.file_storage_path, att.stored_name)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except OSError:
                pass

    # 서브태스크 먼저 삭제 (cascade: logs, attachments)
    for subtask in list(task.subtasks):
        db.delete(subtask)
    db.flush()

    db.delete(task)
    db.commit()


@router.patch("/{task_id}/comments/{log_id}")
def update_comment(
    task_id: int,
    log_id: int,
    req: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(TaskLog).filter(
        TaskLog.id == log_id,
        TaskLog.task_id == task_id,
        TaskLog.action == "comment",
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 댓글만 수정할 수 있습니다.")
    if not req.comment.strip():
        raise HTTPException(status_code=400, detail="댓글 내용을 입력해주세요.")
    log.comment = req.comment.strip()
    db.commit()
    return {"message": "댓글이 수정되었습니다."}


@router.delete("/{task_id}/comments/{log_id}", status_code=204)
def delete_comment(
    task_id: int,
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(TaskLog).filter(
        TaskLog.id == log_id,
        TaskLog.task_id == task_id,
        TaskLog.action == "comment",
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if log.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="본인 댓글만 삭제할 수 있습니다.")
    db.delete(log)
    db.commit()
