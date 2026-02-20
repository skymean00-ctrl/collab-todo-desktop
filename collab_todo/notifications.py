"""
알림 조회 및 상태 변경 리포지토리.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from mysql.connector.connection import MySQLConnection

from .models import Notification
from .repositories.notification_repo import _row_to_notification


def list_unread_notifications(conn: MySQLConnection, user_id: int) -> List[Notification]:
    if user_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id,
                   recipient_id,
                   task_id,
                   notification_type,
                   message,
                   is_read,
                   created_at,
                   read_at
              FROM notifications
             WHERE recipient_id = %s
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
    conn: MySQLConnection,
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

    # 파라미터화된 쿼리 사용 (IN 절도 파라미터화)
    placeholders = ", ".join(["%s"] * len(effective_ids))
    # read_at_value를 첫 번째 파라미터로, 그 다음 ID들을 추가
    params = [read_at_value] + effective_ids

    cursor = conn.cursor()
    try:
        # 파라미터화된 쿼리로 변경 (f-string 제거)
        query = f"""
            UPDATE notifications
               SET is_read = 1,
                   read_at = %s
             WHERE id IN ({placeholders})
            """
        cursor.execute(query, tuple(params))
    finally:
        cursor.close()


