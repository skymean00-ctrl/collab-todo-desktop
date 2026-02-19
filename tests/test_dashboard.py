from datetime import datetime, timedelta

from collab_todo.dashboard import summarize_tasks
from collab_todo.models import Task


def _make_task(status: str, *, delta_days: int | None) -> Task:
    now = datetime.utcnow()
    due_date = None
    if delta_days is not None:
        due_date = now + timedelta(days=delta_days)

    return Task(
        id=1,
        project_id=1,
        parent_task_id=None,
        title="t",
        description=None,
        author_id=1,
        current_assignee_id=1,
        next_assignee_id=None,
        status=status,  # type: ignore[arg-type]
        due_date=due_date,
        confirmed_at=None,
        promised_date=None,
        is_private=False,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )


def test_summarize_tasks_counts_and_due_flags():
    now = datetime.utcnow()

    tasks = [
        _make_task("pending", delta_days=0),     # due today -> due_soon
        _make_task("in_progress", delta_days=-1),  # overdue
        _make_task("review", delta_days=2),     # future, not soon
        _make_task("completed", delta_days=-5),  # completed, not counted in due
    ]

    summary = summarize_tasks(tasks, now=now)

    assert summary.total == 4
    assert summary.pending == 1
    assert summary.in_progress == 1
    assert summary.review == 1
    assert summary.completed == 1
    assert summary.due_soon == 1
    assert summary.overdue == 1


