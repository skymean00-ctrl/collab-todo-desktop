"""프로젝트 데이터 접근."""

from __future__ import annotations

from typing import List

from mysql.connector.connection import MySQLConnection

from collab_todo.models import Project


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
    """사용자가 소유한 프로젝트 목록 조회."""
    if user_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, name, description, owner_id, is_archived,
                   created_at, updated_at
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
