"""
대시보드에서 사용할 간단한 통계 계산 헬퍼.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from .models import Task


@dataclass(frozen=True)
class TaskSummary:
    total: int
    pending: int
    confirmed: int
    in_progress: int
    review: int
    on_hold: int
    completed: int
    cancelled: int
    due_soon: int
    overdue: int


def summarize_tasks(tasks: List[Task], *, now: datetime) -> TaskSummary:
    """
    작업 목록에 대한 간단한 집계를 수행한다.
    """
    total = len(tasks)
    pending = 0
    confirmed = 0
    in_progress = 0
    review = 0
    on_hold = 0
    completed = 0
    cancelled = 0
    due_soon = 0
    overdue = 0

    soon_threshold = now + timedelta(days=1)

    for task in tasks:
        if task.status == "pending":
            pending += 1
        elif task.status == "confirmed":
            confirmed += 1
        elif task.status == "in_progress":
            in_progress += 1
        elif task.status == "review":
            review += 1
        elif task.status == "on_hold":
            on_hold += 1
        elif task.status == "completed":
            completed += 1
        elif task.status == "cancelled":
            cancelled += 1

        if task.due_date is not None and task.status not in ("completed", "cancelled"):
            if task.due_date < now:
                overdue += 1
            elif task.due_date <= soon_threshold:
                due_soon += 1

    return TaskSummary(
        total=total,
        pending=pending,
        confirmed=confirmed,
        in_progress=in_progress,
        review=review,
        on_hold=on_hold,
        completed=completed,
        cancelled=cancelled,
        due_soon=due_soon,
        overdue=overdue,
    )


