"""첨부파일 도메인 모델."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TaskAttachment:
    id: int
    task_id: int
    uploader_id: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: Optional[str]
    created_at: datetime
