"""비공개 업무 열람 권한 데이터 접근."""

from __future__ import annotations

from typing import List

from mysql.connector.connection import MySQLConnection


def list_viewer_ids(conn: MySQLConnection, task_id: int) -> List[int]:
    """비공개 업무의 열람 가능 사용자 ID 목록."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT user_id FROM task_viewers WHERE task_id = %s",
            (task_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [row[0] for row in rows]


def add_viewer(conn: MySQLConnection, task_id: int, user_id: int) -> None:
    """열람 권한 추가."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT IGNORE INTO task_viewers (task_id, user_id)
            VALUES (%s, %s)
            """,
            (task_id, user_id),
        )
    finally:
        cursor.close()


def add_viewers(conn: MySQLConnection, task_id: int, user_ids: List[int]) -> None:
    """열람 권한 일괄 추가."""
    if not user_ids:
        return

    cursor = conn.cursor()
    try:
        cursor.executemany(
            "INSERT IGNORE INTO task_viewers (task_id, user_id) VALUES (%s, %s)",
            [(task_id, uid) for uid in user_ids],
        )
    finally:
        cursor.close()


def remove_viewer(conn: MySQLConnection, task_id: int, user_id: int) -> None:
    """열람 권한 제거."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM task_viewers WHERE task_id = %s AND user_id = %s",
            (task_id, user_id),
        )
    finally:
        cursor.close()


def can_view_task(
    conn: MySQLConnection, task_id: int, user_id: int
) -> bool:
    """사용자가 해당 업무를 볼 수 있는지 확인."""
    cursor = conn.cursor()
    try:
        # 공개 업무이거나, 지시자/담당자이거나, 열람자 목록에 있는지
        cursor.execute(
            """
            SELECT 1 FROM tasks
             WHERE id = %s
               AND (
                   is_private = 0
                   OR author_id = %s
                   OR current_assignee_id = %s
                   OR EXISTS (
                       SELECT 1 FROM task_viewers
                        WHERE task_id = %s AND user_id = %s
                   )
               )
            """,
            (task_id, user_id, user_id, task_id, user_id),
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()
