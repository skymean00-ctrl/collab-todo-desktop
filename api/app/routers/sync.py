from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/api", tags=["sync"])


# ── 응답 스키마 ──────────────────────────────────────────────

class TaskOut(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str]
    author_id: int
    current_assignee_id: int
    next_assignee_id: Optional[int]
    status: str
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class NotificationOut(BaseModel):
    id: int
    task_id: Optional[int]
    notification_type: str
    message: str
    is_read: bool
    created_at: datetime


class SyncResponse(BaseModel):
    server_time: datetime
    tasks: List[TaskOut]
    notifications: List[NotificationOut]


# ── 엔드포인트 ───────────────────────────────────────────────

@router.get("/sync", response_model=SyncResponse)
def sync(
    last_synced_at: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    현재 사용자의 Task 목록 + 읽지 않은 알림을 반환합니다.
    last_synced_at 이 있으면 그 이후 변경분만 반환 (증분 동기화).
    """
    user_id = current_user["id"]

    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)

        # 서버 시간
        cursor.execute("SELECT UTC_TIMESTAMP() AS t")
        server_time: datetime = cursor.fetchone()["t"]

        # Task 조회 (증분 동기화 지원)
        if last_synced_at:
            cursor.execute(
                """
                SELECT id, project_id, title, description, author_id,
                       current_assignee_id, next_assignee_id, status,
                       due_date, completed_at, created_at, updated_at
                  FROM tasks
                 WHERE current_assignee_id = %s
                   AND status <> 'completed'
                   AND (updated_at > %s OR created_at > %s)
                 ORDER BY
                     CASE status
                         WHEN 'in_progress' THEN 1 WHEN 'review' THEN 2
                         WHEN 'pending' THEN 3 WHEN 'on_hold' THEN 4
                         ELSE 5 END,
                     due_date IS NULL, due_date ASC
                """,
                (user_id, last_synced_at, last_synced_at),
            )
        else:
            cursor.execute(
                """
                SELECT id, project_id, title, description, author_id,
                       current_assignee_id, next_assignee_id, status,
                       due_date, completed_at, created_at, updated_at
                  FROM tasks
                 WHERE current_assignee_id = %s
                   AND status <> 'completed'
                 ORDER BY
                     CASE status
                         WHEN 'in_progress' THEN 1 WHEN 'review' THEN 2
                         WHEN 'pending' THEN 3 WHEN 'on_hold' THEN 4
                         ELSE 5 END,
                     due_date IS NULL, due_date ASC
                """,
                (user_id,),
            )
        tasks = cursor.fetchall()

        # 읽지 않은 알림
        cursor.execute(
            """
            SELECT id, task_id, notification_type, message, is_read, created_at
              FROM notifications
             WHERE recipient_id = %s AND is_read = 0
             ORDER BY created_at DESC
            """,
            (user_id,),
        )
        notifications = cursor.fetchall()
        cursor.close()

    return SyncResponse(
        server_time=server_time.replace(tzinfo=timezone.utc),
        tasks=[TaskOut(**t) for t in tasks],
        notifications=[NotificationOut(**n) for n in notifications],
    )
