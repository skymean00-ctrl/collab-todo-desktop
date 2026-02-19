"""하위 업무(자료 요청) 데이터 접근."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from mysql.connector.connection import MySQLConnection

from collab_todo.models import Task
from .task_repo import _row_to_task, _TASK_COLUMNS, _ORDER_BY_STATUS


def list_subtasks(conn: MySQLConnection, parent_task_id: int) -> List[Task]:
    """상위 업무의 하위 자료 요청 목록."""
    if parent_task_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            SELECT {_TASK_COLUMNS}
              FROM tasks
             WHERE parent_task_id = %s
            {_ORDER_BY_STATUS}
            """,
            (parent_task_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_task(row) for row in rows]


def create_subtask(
    conn: MySQLConnection,
    *,
    parent_task_id: int,
    project_id: int,
    title: str,
    description: Optional[str],
    author_id: int,
    current_assignee_id: int,
    due_date: Optional[datetime] = None,
    is_private: bool = False,
) -> int:
    """자료 요청(하위 업무) 생성."""
    if parent_task_id <= 0 or project_id <= 0:
        raise ValueError("잘못된 ID 값입니다.")
    if author_id <= 0 or current_assignee_id <= 0:
        raise ValueError("잘못된 ID 값입니다.")
    if not title.strip():
        raise ValueError("제목은 비어 있을 수 없습니다.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO tasks (
                project_id, parent_task_id, title, description,
                author_id, current_assignee_id,
                status, due_date, is_private
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s, %s)
            """,
            (
                project_id,
                parent_task_id,
                title.strip(),
                description,
                author_id,
                current_assignee_id,
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


def count_subtasks(conn: MySQLConnection, parent_task_id: int) -> tuple[int, int]:
    """(전체 건수, 완료 건수) 반환."""
    if parent_task_id <= 0:
        return (0, 0)

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT
                COUNT(*),
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
              FROM tasks
             WHERE parent_task_id = %s
            """,
            (parent_task_id,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return (0, 0)
    return (row[0], int(row[1] or 0))
