"""
리포지토리 레이어.

SQL 문자열을 애플리케이션 전역에 흩뿌리지 않고,
데이터 접근 로직을 한 곳에서 관리한다.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from mysql.connector.connection import MySQLConnection

from .models import User, Project, Task, TaskHistory


def _row_to_user(row: tuple) -> User:
    return User(
        id=row[0],
        username=row[1],
        display_name=row[2],
        email=row[3],
        role=row[4],
        is_active=bool(row[5]),
        created_at=row[6],
        updated_at=row[7],
    )


def get_user_by_id(conn: MySQLConnection, user_id: int) -> Optional[User]:
    if user_id <= 0:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, username, display_name, email, role, is_active, created_at, updated_at
              FROM users
             WHERE id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return None
    return _row_to_user(row)


def list_active_users(conn: MySQLConnection) -> List[User]:
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, username, display_name, email, role, is_active, created_at, updated_at
              FROM users
             WHERE is_active = 1
             ORDER BY display_name ASC
            """
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_user(row) for row in rows]


def _row_to_project(row: tuple) -> Project:
    return Project(
        id=row[0],
        name=row[1],
        description=row[2],
        owner_id=row[3],
        is_archived=bool(row[4]),
        created_at=row[5],
        updated_at=row[6],
    )


def list_projects_for_user(conn: MySQLConnection, user_id: int) -> List[Project]:
    """
    사용자가 소유하거나 멤버로 속한 프로젝트 목록을 조회한다.
    초기 버전에서는 owner 기준으로만 필터한다.
    """
    if user_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, name, description, owner_id, is_archived, created_at, updated_at
              FROM projects
             WHERE owner_id = %s
               AND is_archived = 0
             ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_project(row) for row in rows]


def _row_to_task(row: tuple) -> Task:
    return Task(
        id=row[0],
        project_id=row[1],
        title=row[2],
        description=row[3],
        author_id=row[4],
        current_assignee_id=row[5],
        next_assignee_id=row[6],
        status=row[7],
        due_date=row[8],
        completed_at=row[9],
        created_at=row[10],
        updated_at=row[11],
    )


def list_tasks_for_assignee(
    conn: MySQLConnection,
    user_id: int,
    *,
    include_completed: bool = False,
    last_synced_at: Optional[datetime] = None,
) -> List[Task]:
    """
    담당자 기준으로 Task 목록을 조회한다.
    
    Args:
        conn: 데이터베이스 연결
        user_id: 담당자 사용자 ID
        include_completed: 완료된 작업 포함 여부
        last_synced_at: 마지막 동기화 시각 (None이면 전체 조회, 설정 시 증분 동기화)
    """
    if user_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        # 증분 동기화: last_synced_at이 있으면 변경된 항목만 조회
        if last_synced_at is not None:
            if include_completed:
                cursor.execute(
                    """
                    SELECT id,
                           project_id,
                           title,
                           description,
                           author_id,
                           current_assignee_id,
                           next_assignee_id,
                           status,
                           due_date,
                           completed_at,
                           created_at,
                           updated_at
                      FROM tasks
                     WHERE current_assignee_id = %s
                       AND (updated_at > %s OR created_at > %s)
                     ORDER BY
                         CASE status
                             WHEN 'pending' THEN 1
                             WHEN 'in_progress' THEN 2
                             WHEN 'review' THEN 3
                             WHEN 'on_hold' THEN 4
                             WHEN 'completed' THEN 5
                             ELSE 6
                         END,
                         due_date IS NULL,
                         due_date ASC,
                         created_at DESC
                    """,
                    (user_id, last_synced_at, last_synced_at),
                )
            else:
                cursor.execute(
                    """
                    SELECT id,
                           project_id,
                           title,
                           description,
                           author_id,
                           current_assignee_id,
                           next_assignee_id,
                           status,
                           due_date,
                           completed_at,
                           created_at,
                           updated_at
                      FROM tasks
                     WHERE current_assignee_id = %s
                       AND status <> 'completed'
                       AND (updated_at > %s OR created_at > %s)
                     ORDER BY
                         CASE status
                             WHEN 'pending' THEN 1
                             WHEN 'in_progress' THEN 2
                             WHEN 'review' THEN 3
                             WHEN 'on_hold' THEN 4
                             WHEN 'completed' THEN 5
                             ELSE 6
                         END,
                         due_date IS NULL,
                         due_date ASC,
                         created_at DESC
                    """,
                    (user_id, last_synced_at, last_synced_at),
                )
        elif include_completed:
            cursor.execute(
                """
                SELECT id,
                       project_id,
                       title,
                       description,
                       author_id,
                       current_assignee_id,
                       next_assignee_id,
                       status,
                       due_date,
                       completed_at,
                       created_at,
                       updated_at
                  FROM tasks
                 WHERE current_assignee_id = %s
                 ORDER BY
                     CASE status
                         WHEN 'pending' THEN 1
                         WHEN 'in_progress' THEN 2
                         WHEN 'review' THEN 3
                         WHEN 'on_hold' THEN 4
                         WHEN 'completed' THEN 5
                         ELSE 6
                     END,
                     due_date IS NULL,
                     due_date ASC,
                     created_at DESC
                """,
                (user_id,),
            )
        else:
            cursor.execute(
                """
                SELECT id,
                       project_id,
                       title,
                       description,
                       author_id,
                       current_assignee_id,
                       next_assignee_id,
                       status,
                       due_date,
                       completed_at,
                       created_at,
                       updated_at
                  FROM tasks
                 WHERE current_assignee_id = %s
                   AND status <> 'completed'
                 ORDER BY
                     CASE status
                         WHEN 'pending' THEN 1
                         WHEN 'in_progress' THEN 2
                         WHEN 'review' THEN 3
                         WHEN 'on_hold' THEN 4
                         WHEN 'completed' THEN 5
                         ELSE 6
                     END,
                     due_date IS NULL,
                     due_date ASC,
                     created_at DESC
                """,
                (user_id,),
            )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_task(row) for row in rows]


def list_tasks_created_by_user(conn: MySQLConnection, user_id: int) -> List[Task]:
    """
    사용자가 작성자로 되어 있는 Task 목록을 조회한다.
    """
    if user_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id,
                   project_id,
                   title,
                   description,
                   author_id,
                   current_assignee_id,
                   next_assignee_id,
                   status,
                   due_date,
                   completed_at,
                   created_at,
                   updated_at
              FROM tasks
             WHERE author_id = %s
             ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_task(row) for row in rows]


def _row_to_task_history(row: tuple) -> TaskHistory:
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
    """
    단일 Task에 대한 이력(타임라인)을 시간순으로 반환한다.
    """
    if task_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id,
                   task_id,
                   actor_id,
                   action_type,
                   old_status,
                   new_status,
                   note,
                   created_at
              FROM task_history
             WHERE task_id = %s
             ORDER BY created_at ASC
            """,
            (task_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_task_history(row) for row in rows]



def create_task(
    conn: MySQLConnection,
    *,
    project_id: int,
    title: str,
    description: Optional[str],
    author_id: int,
    current_assignee_id: int,
    next_assignee_id: Optional[int],
    due_date,
) -> int:
    """
    새 Task를 생성한다.

    - 기본 상태는 'pending'
    - 필수 ID 값이 0 이하인 경우 예외를 발생시켜 조기 실패하게 한다.
    """
    if project_id <= 0 or author_id <= 0 or current_assignee_id <= 0:
        raise ValueError("잘못된 ID 값입니다.")

    if not title.strip():
        raise ValueError("제목은 비어 있을 수 없습니다.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO tasks (
                project_id,
                title,
                description,
                author_id,
                current_assignee_id,
                next_assignee_id,
                status,
                due_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)
            """,
            (
                project_id,
                title.strip(),
                description,
                author_id,
                current_assignee_id,
                next_assignee_id,
                due_date,
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
    """
    Task 상태를 변경한다.

    - 이미 completed/cancelled 인 Task는 변경하지 않는다.
    - 상태 변경 기록은 task_history에 남긴다.
    """
    if task_id <= 0 or actor_id <= 0:
        raise ValueError("잘못된 ID 값입니다.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT status
              FROM tasks
             WHERE id = %s
             FOR UPDATE
            """,
            (task_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError("Task를 찾을 수 없습니다.")

        old_status = row[0]
        if old_status in ("completed", "cancelled"):
            # 이미 종료된 Task는 상태 변경하지 않음
            return

        cursor.execute(
            """
            UPDATE tasks
               SET status = %s
             WHERE id = %s
            """,
            (new_status, task_id),
        )

        cursor.execute(
            """
            INSERT INTO task_history (
                task_id,
                actor_id,
                action_type,
                old_status,
                new_status
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (task_id, actor_id, "status_change", old_status, new_status),
        )
    finally:
        cursor.close()


def complete_task_and_move_to_next(
    conn: MySQLConnection,
    *,
    task_id: int,
    actor_id: int,
) -> None:
    """
    Task를 완료 처리하고, 다음 담당자가 있으면 그 사람에게 업무를 넘긴다.

    - next_assignee_id 가 NULL이면 최종 완료로 간주한다.
    - 완료 기록을 task_history에 남긴다.
    """
    if task_id <= 0 or actor_id <= 0:
        raise ValueError("잘못된 ID 값입니다.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT status, next_assignee_id
              FROM tasks
             WHERE id = %s
             FOR UPDATE
            """,
            (task_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError("Task를 찾을 수 없습니다.")

        current_status, next_assignee_id = row
        if current_status in ("completed", "cancelled"):
            return

        if next_assignee_id is None:
            # 최종 완료
            new_status = "completed"
            cursor.execute(
                """
                UPDATE tasks
                   SET status = %s,
                       completed_at = NOW()
                 WHERE id = %s
                """,
                (new_status, task_id),
            )
        else:
            # 다음 담당자에게 전달, 상태는 review로 설정
            new_status = "review"
            cursor.execute(
                """
                UPDATE tasks
                   SET current_assignee_id = %s,
                       status = %s
                 WHERE id = %s
                """,
                (next_assignee_id, new_status, task_id),
            )

        cursor.execute(
            """
            INSERT INTO task_history (
                task_id,
                actor_id,
                action_type,
                old_status,
                new_status
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (task_id, actor_id, "complete_or_forward", current_status, new_status),
        )
    finally:
        cursor.close()



