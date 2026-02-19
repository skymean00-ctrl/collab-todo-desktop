"""업무 데이터 접근 (최상위 업무 CRUD)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from mysql.connector.connection import MySQLConnection

from collab_todo.models import Task


_TASK_COLUMNS = """
    id, project_id, parent_task_id, title, description,
    author_id, current_assignee_id, next_assignee_id,
    status, due_date, confirmed_at, promised_date,
    is_private, completed_at, created_at, updated_at
"""

_ORDER_BY_STATUS = """
    ORDER BY
        CASE status
            WHEN 'pending' THEN 1
            WHEN 'confirmed' THEN 2
            WHEN 'in_progress' THEN 3
            WHEN 'review' THEN 4
            WHEN 'on_hold' THEN 5
            WHEN 'completed' THEN 6
            ELSE 7
        END,
        due_date IS NULL,
        due_date ASC,
        created_at DESC
"""


def _row_to_task(row: tuple) -> Task:
    return Task(
        id=row[0],
        project_id=row[1],
        parent_task_id=row[2],
        title=row[3],
        description=row[4],
        author_id=row[5],
        current_assignee_id=row[6],
        next_assignee_id=row[7],
        status=row[8],
        due_date=row[9],
        confirmed_at=row[10],
        promised_date=row[11],
        is_private=bool(row[12]),
        completed_at=row[13],
        created_at=row[14],
        updated_at=row[15],
    )


def get_task_by_id(conn: MySQLConnection, task_id: int) -> Optional[Task]:
    if task_id <= 0:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute(
            f"SELECT {_TASK_COLUMNS} FROM tasks WHERE id = %s",
            (task_id,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return None
    return _row_to_task(row)


def list_tasks_for_assignee(
    conn: MySQLConnection,
    user_id: int,
    *,
    include_completed: bool = False,
    last_synced_at: Optional[datetime] = None,
) -> List[Task]:
    """담당자 기준 업무 목록 (최상위 업무만, parent_task_id IS NULL)."""
    if user_id <= 0:
        return []

    conditions = ["current_assignee_id = %s", "parent_task_id IS NULL"]
    params: list = [user_id]

    if not include_completed:
        conditions.append("status NOT IN ('completed', 'cancelled')")

    if last_synced_at is not None:
        conditions.append("(updated_at > %s OR created_at > %s)")
        params.extend([last_synced_at, last_synced_at])

    where = " AND ".join(conditions)

    cursor = conn.cursor()
    try:
        cursor.execute(
            f"SELECT {_TASK_COLUMNS} FROM tasks WHERE {where} {_ORDER_BY_STATUS}",
            tuple(params),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_task(row) for row in rows]


def list_tasks_created_by_user(
    conn: MySQLConnection,
    user_id: int,
    *,
    include_completed: bool = False,
) -> List[Task]:
    """지시자 기준 업무 목록 (최상위 업무만)."""
    if user_id <= 0:
        return []

    conditions = ["author_id = %s", "parent_task_id IS NULL"]
    params: list = [user_id]

    if not include_completed:
        conditions.append("status NOT IN ('completed', 'cancelled')")

    where = " AND ".join(conditions)

    cursor = conn.cursor()
    try:
        cursor.execute(
            f"SELECT {_TASK_COLUMNS} FROM tasks WHERE {where} {_ORDER_BY_STATUS}",
            tuple(params),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_task(row) for row in rows]


def create_task(
    conn: MySQLConnection,
    *,
    project_id: int,
    title: str,
    description: Optional[str],
    author_id: int,
    current_assignee_id: int,
    next_assignee_id: Optional[int] = None,
    due_date: Optional[datetime] = None,
    is_private: bool = False,
) -> int:
    """새 업무를 생성한다. 기본 상태는 'pending'."""
    if project_id <= 0 or author_id <= 0 or current_assignee_id <= 0:
        raise ValueError("잘못된 ID 값입니다.")
    if not title.strip():
        raise ValueError("제목은 비어 있을 수 없습니다.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO tasks (
                project_id, title, description,
                author_id, current_assignee_id, next_assignee_id,
                status, due_date, is_private
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s, %s)
            """,
            (
                project_id,
                title.strip(),
                description,
                author_id,
                current_assignee_id,
                next_assignee_id,
                due_date,
                int(is_private),
            ),
        )
        task_id = cursor.lastrowid
    finally:
        cursor.close()

    if not isinstance(task_id, int) or task_id <= 0:
        raise RuntimeError("Task ID를 가져오지 못했습니다.")
    return task_id


def update_task_status(
    conn: MySQLConnection,
    *,
    task_id: int,
    actor_id: int,
    new_status: str,
) -> None:
    """업무 상태 변경 + 이력 기록."""
    if task_id <= 0 or actor_id <= 0:
        raise ValueError("잘못된 ID 값입니다.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT status FROM tasks WHERE id = %s FOR UPDATE",
            (task_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError("업무를 찾을 수 없습니다.")

        old_status = row[0]
        if old_status in ("completed", "cancelled"):
            return

        cursor.execute(
            "UPDATE tasks SET status = %s WHERE id = %s",
            (new_status, task_id),
        )
        cursor.execute(
            """
            INSERT INTO task_history (task_id, actor_id, action_type, old_status, new_status)
            VALUES (%s, %s, 'status_change', %s, %s)
            """,
            (task_id, actor_id, old_status, new_status),
        )
    finally:
        cursor.close()


def confirm_task(
    conn: MySQLConnection,
    *,
    task_id: int,
    actor_id: int,
    promised_date: datetime,
) -> None:
    """업무 확인 + 기한 약속."""
    if task_id <= 0 or actor_id <= 0:
        raise ValueError("잘못된 ID 값입니다.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT status FROM tasks WHERE id = %s FOR UPDATE",
            (task_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError("업무를 찾을 수 없습니다.")

        old_status = row[0]
        if old_status != "pending":
            return

        cursor.execute(
            """
            UPDATE tasks
               SET status = 'confirmed',
                   confirmed_at = NOW(),
                   promised_date = %s
             WHERE id = %s
            """,
            (promised_date, task_id),
        )
        cursor.execute(
            """
            INSERT INTO task_history (task_id, actor_id, action_type, old_status, new_status, note)
            VALUES (%s, %s, 'confirm', %s, 'confirmed', %s)
            """,
            (task_id, actor_id, old_status,
             f"약속일: {promised_date.strftime('%Y-%m-%d')}"),
        )
    finally:
        cursor.close()


def complete_task(
    conn: MySQLConnection,
    *,
    task_id: int,
    actor_id: int,
) -> None:
    """업무 완료 처리."""
    if task_id <= 0 or actor_id <= 0:
        raise ValueError("잘못된 ID 값입니다.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT status, next_assignee_id FROM tasks WHERE id = %s FOR UPDATE",
            (task_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError("업무를 찾을 수 없습니다.")

        current_status, next_assignee_id = row
        if current_status in ("completed", "cancelled"):
            return

        if next_assignee_id is None:
            new_status = "completed"
            cursor.execute(
                "UPDATE tasks SET status = %s, completed_at = NOW() WHERE id = %s",
                (new_status, task_id),
            )
        else:
            new_status = "review"
            cursor.execute(
                """
                UPDATE tasks SET current_assignee_id = %s, status = %s WHERE id = %s
                """,
                (next_assignee_id, new_status, task_id),
            )

        cursor.execute(
            """
            INSERT INTO task_history (task_id, actor_id, action_type, old_status, new_status)
            VALUES (%s, %s, 'complete_or_forward', %s, %s)
            """,
            (task_id, actor_id, current_status, new_status),
        )
    finally:
        cursor.close()
