"""첨부파일 데이터 접근."""

from __future__ import annotations

from typing import List, Optional

from mysql.connector.connection import MySQLConnection

from collab_todo.models import TaskAttachment


def _row_to_attachment(row: tuple) -> TaskAttachment:
    return TaskAttachment(
        id=row[0],
        task_id=row[1],
        uploader_id=row[2],
        file_name=row[3],
        file_path=row[4],
        file_size=row[5],
        mime_type=row[6],
        created_at=row[7],
    )


def list_attachments(conn: MySQLConnection, task_id: int) -> List[TaskAttachment]:
    """업무의 첨부파일 목록."""
    if task_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, task_id, uploader_id, file_name, file_path,
                   file_size, mime_type, created_at
              FROM task_attachments
             WHERE task_id = %s
             ORDER BY created_at ASC
            """,
            (task_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_attachment(row) for row in rows]


def list_attachments_with_subtasks(
    conn: MySQLConnection, task_id: int
) -> List[TaskAttachment]:
    """업무 + 하위 자료요청의 첨부파일 전체."""
    if task_id <= 0:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT a.id, a.task_id, a.uploader_id, a.file_name, a.file_path,
                   a.file_size, a.mime_type, a.created_at
              FROM task_attachments a
              JOIN tasks t ON a.task_id = t.id
             WHERE t.id = %s OR t.parent_task_id = %s
             ORDER BY a.created_at ASC
            """,
            (task_id, task_id),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [_row_to_attachment(row) for row in rows]


def create_attachment(
    conn: MySQLConnection,
    *,
    task_id: int,
    uploader_id: int,
    file_name: str,
    file_path: str,
    file_size: int,
    mime_type: Optional[str] = None,
) -> int:
    """첨부파일 레코드 생성."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO task_attachments
                (task_id, uploader_id, file_name, file_path, file_size, mime_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (task_id, uploader_id, file_name, file_path, file_size, mime_type),
        )
        attachment_id = cursor.lastrowid
    finally:
        cursor.close()

    return attachment_id


def delete_attachment(conn: MySQLConnection, attachment_id: int) -> None:
    """첨부파일 레코드 삭제."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM task_attachments WHERE id = %s",
            (attachment_id,),
        )
    finally:
        cursor.close()
