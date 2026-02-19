"""업무 도메인 모델."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal


TaskStatus = Literal[
    "pending",
    "confirmed",
    "in_progress",
    "review",
    "completed",
    "on_hold",
    "cancelled",
]


@dataclass(frozen=True)
class Task:
    id: int
    project_id: int
    parent_task_id: Optional[int]
    title: str
    description: Optional[str]
    author_id: int
    current_assignee_id: int
    next_assignee_id: Optional[int]
    status: TaskStatus
    due_date: Optional[datetime]
    confirmed_at: Optional[datetime]
    promised_date: Optional[datetime]
    is_private: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
