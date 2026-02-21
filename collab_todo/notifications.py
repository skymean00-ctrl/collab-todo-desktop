"""
알림 조회 및 상태 변경 리포지토리.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional

from .models import Notification


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


def list_unread_notifications(conn: sqlite3.Connection, user_id: int) -> List[Notification]:
    if user_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, recipient_id, task_id, notification_type,
                   message, is_read, created_at, read_at
              FROM notifications
             WHERE recipient_id = ?
               AND is_read = 0
             ORDER BY created_at ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_notification(row) for row in rows]


def mark_notifications_as_read(
    conn: sqlite3.Connection,
    notification_ids: List[int],
    *,
    read_at: Optional[datetime] = None,
) -> None:
    """
    알림을 읽음 처리한다.

    Args:
        conn: 데이터베이스 연결
        notification_ids: 읽음 처리할 알림 ID 목록
        read_at: 읽은 시각 (None이면 현재 시각 사용)
    """
    if not notification_ids:
        return

    effective_ids = [nid for nid in notification_ids if nid > 0]
    if not effective_ids:
        return

    read_at_value = read_at or datetime.utcnow()
    placeholders = ", ".join(["?"] * len(effective_ids))
    params = [read_at_value] + effective_ids

    cursor = conn.cursor()
    try:
        query = f"""
            UPDATE notifications
               SET is_read = 1,
                   read_at = ?
             WHERE id IN ({placeholders})
            """
        cursor.execute(query, tuple(params))
    finally:
        cursor.close()
