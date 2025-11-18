"""
핵심 워크플로우(작업 생성, 상태 변경, 순차 위임) 단위 테스트 스크립트.

실제 MySQL에 연결하여 가장 단순한 happy path를 검증한다.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from collab_todo.config import load_db_config
from collab_todo.db import db_connection
from collab_todo.repositories import (
    create_task,
    update_task_status,
    complete_task_and_move_to_next,
)


def main() -> int:
    config = load_db_config()
    if config is None:
        print("DB 설정이 완료되지 않았습니다. 핵심 워크플로우 테스트를 건너뜁니다.")
        return 1

    # 테스트에 사용할 임시 값들 (실제 환경에서는 사전에 존재해야 함)
    project_id = 1
    author_id = 1
    current_assignee_id = 1
    next_assignee_id = None

    due_date = datetime.utcnow() + timedelta(days=3)

    with db_connection(config) as conn:
        task_id = create_task(
            conn,
            project_id=project_id,
            title="[TEST] 핵심 워크플로우 작업",
            description="테스트용 작업입니다.",
            author_id=author_id,
            current_assignee_id=current_assignee_id,
            next_assignee_id=next_assignee_id,
            due_date=due_date,
        )

        update_task_status(
            conn,
            task_id=task_id,
            actor_id=current_assignee_id,
            new_status="in_progress",
        )

        complete_task_and_move_to_next(
            conn,
            task_id=task_id,
            actor_id=current_assignee_id,
        )

    print("핵심 워크플로우 테스트 스크립트가 예외 없이 완료되었습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


