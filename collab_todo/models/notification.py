"""알림 도메인 모델."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
