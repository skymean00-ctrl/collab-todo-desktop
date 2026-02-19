"""업무 이력 데이터 접근."""

from __future__ import annotations

from typing import List

from mysql.connector.connection import MySQLConnection

from collab_todo.models import TaskHistory


def _row_to_history(row: tuple) -> TaskHistory:
    return TaskHistory(
        id=row[0],
        task_id=row[1],
        actor_id=row[2],
        action_type=row[3],
        old_status=row[4],
        new_status=row[5],
        note=row[6],
        created_at=row[7],
    )


def list_task_history(conn: MySQLConnection, task_id: int) -> List[TaskHistory]:
    """업무의 이력(타임라인)을 시간순으로 반환."""
    if task_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, task_id, actor_id, action_type,
                   old_status, new_status, note, created_at
              FROM task_history
             WHERE task_id = %s
             ORDER BY created_at ASC
            """,
            (task_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_history(row) for row in rows]
