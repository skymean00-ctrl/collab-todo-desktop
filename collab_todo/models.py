"""
도메인 모델 정의.

DB 레코드를 직접 노출하지 않고, 애플리케이션 내부에서 사용할
타입 안정성이 있는 데이터 구조를 제공한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal


UserRole = Literal["user", "admin", "supervisor"]
TaskStatus = Literal["pending", "in_progress", "review", "completed", "on_hold", "cancelled"]


@dataclass(frozen=True)
class User:
    id: int
    username: str
    display_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Project:
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Task:
    id: int
    project_id: int
    title: str
    description: Optional[str]
    author_id: int
    current_assignee_id: int
    next_assignee_id: Optional[int]
    status: TaskStatus
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TaskHistory:
    id: int
    task_id: int
    actor_id: int
    action_type: str
    old_status: Optional[str]
    new_status: Optional[str]
    note: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class Notification:
    id: int
    recipient_id: int
    task_id: Optional[int]
    notification_type: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]


