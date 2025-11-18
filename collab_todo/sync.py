"""
주기적 동기화(폴링)용 헬퍼.

클라이언트는 마지막 동기화 시각을 기억하고,
이 모듈을 통해 변경된 Task/알림을 가져온다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from mysql.connector.connection import MySQLConnection

from .models import Task, Notification
from .repositories import list_tasks_for_assignee
from .notifications import list_unread_notifications


@dataclass(frozen=True)
class SyncState:
    """
    클라이언트가 유지하는 최소 동기화 상태.

    - last_synced_at: 마지막으로 서버와 동기화한 시각(UTC)
    """

    last_synced_at: Optional[datetime]


@dataclass(frozen=True)
class SyncResult:
    """
    한 번의 동기화 결과.

    - tasks: 현재 담당자인 Task 목록
    - notifications: 아직 읽지 않은 알림 목록
    - server_time: 서버 기준 현재 시각
    """

    tasks: List[Task]
    notifications: List[Notification]
    server_time: datetime


def perform_sync(
    conn: MySQLConnection,
    *,
    user_id: int,
    state: SyncState,
) -> Tuple[SyncResult, SyncState]:
    """
    주어진 사용자에 대해 한 번의 동기화를 수행한다.

    증분 동기화 지원:
    - last_synced_at이 설정되어 있으면 변경된 Task만 조회 (성능 최적화)
    - 첫 동기화이거나 last_synced_at이 None이면 전체 목록 조회
    - 알림은 항상 미확인(not read) 목록만 가져온다.
    """
    if user_id <= 0:
        raise ValueError("잘못된 사용자 ID 입니다.")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT UTC_TIMESTAMP()")
        row = cursor.fetchone()
    finally:
        cursor.close()

    if not row or not isinstance(row[0], datetime):
        raise RuntimeError("서버 시간을 가져오지 못했습니다.")

    server_time: datetime = row[0]

    # 증분 동기화: last_synced_at이 있으면 변경된 항목만 조회
    tasks = list_tasks_for_assignee(
        conn,
        user_id=user_id,
        include_completed=False,
        last_synced_at=state.last_synced_at,
    )
    notifications = list_unread_notifications(conn, user_id=user_id)

    result = SyncResult(
        tasks=tasks,
        notifications=notifications,
        server_time=server_time,
    )

    new_state = SyncState(last_synced_at=server_time)
    return result, new_state


