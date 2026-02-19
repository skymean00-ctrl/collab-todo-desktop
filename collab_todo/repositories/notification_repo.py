"""알림 데이터 접근."""

from __future__ import annotations

from typing import List, Optional

from mysql.connector.connection import MySQLConnection

from collab_todo.models import Notification


def _row_to_notification(row: tuple) -> Notification:
    return Notification(
        id=row[0],
        recipient_id=row[1],
        task_id=row[2],
        notification_type=row[3],
        message=row[4],
        is_read=bool(row[5]),
        created_at=row[6],
        read_at=row[7],
    )


def list_notifications(
    conn: MySQLConnection,
    user_id: int,
    *,
    unread_only: bool = False,
    limit: int = 50,
) -> List[Notification]:
    """사용자의 알림 목록."""
    conditions = ["recipient_id = %s"]
    params: list = [user_id]

    if unread_only:
        conditions.append("is_read = 0")

    where = " AND ".join(conditions)

    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            SELECT id, recipient_id, task_id, notification_type,
                   message, is_read, created_at, read_at
              FROM notifications
             WHERE {where}
             ORDER BY created_at DESC
             LIMIT %s
            """,
            (*params, limit),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_notification(row) for row in rows]


def count_unread(conn: MySQLConnection, user_id: int) -> int:
    """안 읽은 알림 수."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM notifications WHERE recipient_id = %s AND is_read = 0",
            (user_id,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    return row[0] if row else 0


def create_notification(
    conn: MySQLConnection,
    *,
    recipient_id: int,
    task_id: Optional[int],
    notification_type: str,
    message: str,
) -> int:
    """알림 생성."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO notifications (recipient_id, task_id, notification_type, message)
            VALUES (%s, %s, %s, %s)
            """,
            (recipient_id, task_id, notification_type, message),
        )
        noti_id = cursor.lastrowid
    finally:
        cursor.close()

    return noti_id


def mark_as_read(conn: MySQLConnection, notification_id: int) -> None:
    """알림 읽음 처리."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE notifications SET is_read = 1, read_at = NOW() WHERE id = %s",
            (notification_id,),
        )
    finally:
        cursor.close()


def mark_all_as_read(conn: MySQLConnection, user_id: int) -> None:
    """모든 알림 읽음 처리."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE notifications
               SET is_read = 1, read_at = NOW()
             WHERE recipient_id = %s AND is_read = 0
            """,
            (user_id,),
        )
    finally:
        cursor.close()
