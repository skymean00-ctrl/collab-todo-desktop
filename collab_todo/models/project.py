"""프로젝트 도메인 모델."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Project:
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
