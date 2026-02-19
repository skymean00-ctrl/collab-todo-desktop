"""업무 이력 도메인 모델."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
