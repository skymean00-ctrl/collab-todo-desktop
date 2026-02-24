from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional

from ..auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/unread-count")
def unread_count(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS cnt FROM notifications WHERE recipient_id=%s AND is_read=0", (uid,))
        count = cursor.fetchone()["cnt"]
        cursor.close()
    return {"count": count}


@router.get("/")
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["id"]
    offset = (page - 1) * page_size
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS cnt FROM notifications WHERE recipient_id=%s", (uid,))
        total = cursor.fetchone()["cnt"]
        cursor.execute("""
            SELECT id, task_id, notification_type, message, is_read, created_at
              FROM notifications
             WHERE recipient_id = %s
             ORDER BY created_at DESC
             LIMIT %s OFFSET %s
        """, (uid, page_size, offset))
        items = cursor.fetchall()
        cursor.close()
    return {
        "items": [
            {
                "id": r["id"],
                "task_id": r["task_id"],
                "notification_type": r["notification_type"],
                "message": r["message"],
                "is_read": bool(r["is_read"]),
                "created_at": r["created_at"].isoformat(),
            }
            for r in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read=1 WHERE id=%s AND recipient_id=%s",
            (notification_id, uid)
        )
        conn.commit()
        cursor.close()
    return {"ok": True}


@router.post("/read-all")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read=1 WHERE recipient_id=%s AND is_read=0", (uid,))
        conn.commit()
        cursor.close()
    return {"ok": True}
