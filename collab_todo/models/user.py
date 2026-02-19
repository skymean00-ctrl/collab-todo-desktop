"""사용자 도메인 모델."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


UserRole = Literal["user", "admin", "supervisor"]


@dataclass(frozen=True)
class User:
    id: int
    username: str
    display_name: str
    email: str
    position: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
