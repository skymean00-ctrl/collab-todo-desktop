from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

VALID_STATUSES = {"pending", "in_progress", "review", "approved", "rejected"}
VALID_PRIORITIES = {"low", "normal", "high", "urgent"}
VALID_SORT_FIELDS = {"created_at", "updated_at", "due_date", "title", "priority", "status"}


# ── 공통 헬퍼 ────────────────────────────────────────────────

def _get_task_row(cursor, task_id: int, user_id: int):
    cursor.execute("""
        SELECT t.id, t.title, t.description, t.status, t.priority, t.progress,
               t.due_date, t.created_at, t.updated_at,
               t.author_id, t.current_assignee_id,
               a.display_name AS assigner_name,
               b.display_name AS assignee_name,
               (SELECT COUNT(*) FROM task_attachments ta WHERE ta.task_id = t.id) AS attachment_count,
               EXISTS(SELECT 1 FROM task_favorites tf WHERE tf.task_id = t.id AND tf.user_id = %s) AS is_favorite
          FROM tasks t
          LEFT JOIN users a ON a.id = t.author_id
          LEFT JOIN users b ON b.id = t.current_assignee_id
         WHERE t.id = %s
    """, (user_id, task_id))
    return cursor.fetchone()


def _format_task(row: dict) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row.get("description"),
        "content": row.get("description"),  # frontend alias
        "status": row["status"],
        "priority": row.get("priority", "normal"),
        "progress": row.get("progress", 0),
        "due_date": row["due_date"].strftime("%Y-%m-%d") if row.get("due_date") else None,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
        "is_favorite": bool(row.get("is_favorite", 0)),
        "attachment_count": row.get("attachment_count", 0),
        "subtask_count": 0,
        "subtasks_done": 0,
        "tags": [],
        "assigner": {"id": row.get("author_id"), "name": row.get("assigner_name") or ""},
        "assignee": {"id": row.get("current_assignee_id"), "name": row.get("assignee_name") or ""},
        "author_id": row.get("author_id"),
        "current_assignee_id": row.get("current_assignee_id"),
        "attachments": [],  # populated by get_task
        "subtasks": [],     # no parent_task_id column in DB
        "estimated_hours": None,
        "category": None,
    }


# ── 요청 스키마 ────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    content: Optional[str] = None
    assignee_id: int
    category_id: Optional[int] = None
    priority: str = "normal"
    estimated_hours: Optional[float] = None
    due_date: Optional[str] = None
    tag_names: List[str] = []
    is_subtask: bool = False
    parent_task_id: Optional[int] = None
    material_providers: List[dict] = []


class StatusUpdate(BaseModel):
    status: str
    comment: Optional[str] = None


class TaskPatch(BaseModel):
    progress: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    assignee_id: Optional[int] = None


class BulkStatusRequest(BaseModel):
    task_ids: List[int]
    status: str
    comment: Optional[str] = None


class ReassignRequest(BaseModel):
    assignee_id: int


# ── 엔드포인트 ─────────────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT COUNT(*) AS total,
                   SUM(priority='urgent') AS urgent,
                   SUM(due_date IS NOT NULL AND due_date > NOW()
                       AND DATEDIFF(due_date, NOW()) <= 3
                       AND status NOT IN ('approved','rejected')) AS due_soon,
                   SUM(due_date IS NOT NULL AND due_date < NOW()
                       AND status NOT IN ('approved','rejected')) AS overdue,
                   SUM(status='rejected') AS rejected
              FROM tasks
             WHERE current_assignee_id = %s AND status NOT IN ('approved')
        """, (uid,))
        summary = cursor.fetchone()

        cursor.execute("""
            SELECT status, COUNT(*) AS cnt
              FROM tasks
             WHERE current_assignee_id = %s
             GROUP BY status
        """, (uid,))
        breakdown = {row["status"]: row["cnt"] for row in cursor.fetchall()}
        cursor.close()

    return {
        "total": int(summary["total"] or 0),
        "urgent": int(summary["urgent"] or 0),
        "due_soon": int(summary["due_soon"] or 0),
        "overdue": int(summary["overdue"] or 0),
        "rejected": int(summary["rejected"] or 0),
        "status_breakdown": breakdown,
    }


@router.get("/")
def list_tasks(
    section: str = Query("assigned_to_me"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    due_date_from: Optional[str] = Query(None),
    due_date_to: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    favorites_only: bool = Query(False),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["id"]
    if sort_by not in VALID_SORT_FIELDS:
        sort_by = "created_at"
    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"

    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        where = []
        params = []

        if section == "assigned_to_me":
            where.append("t.current_assignee_id = %s"); params.append(uid)
        elif section == "assigned_by_me":
            where.append("t.author_id = %s"); params.append(uid)
        elif section == "subtasks_to_me":
            where.append("t.current_assignee_id = %s"); params.append(uid)
        else:
            where.append("(t.current_assignee_id = %s OR t.author_id = %s)")
            params.extend([uid, uid])

        if status: where.append("t.status = %s"); params.append(status)
        if priority: where.append("t.priority = %s"); params.append(priority)
        if search:
            where.append("(t.title LIKE %s OR t.description LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        if due_date_from: where.append("DATE(t.due_date) >= %s"); params.append(due_date_from)
        if due_date_to: where.append("DATE(t.due_date) <= %s"); params.append(due_date_to)
        if favorites_only:
            where.append("EXISTS(SELECT 1 FROM task_favorites tf WHERE tf.task_id=t.id AND tf.user_id=%s)")
            params.append(uid)

        where_sql = "WHERE " + " AND ".join(where) if where else ""

        cursor.execute(f"SELECT COUNT(*) AS cnt FROM tasks t {where_sql}", params)
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * page_size
        cursor.execute(f"""
            SELECT t.id, t.title, t.description, t.status, t.priority, t.progress,
                   t.due_date, t.created_at, t.updated_at,
                   t.author_id, t.current_assignee_id,
                   a.display_name AS assigner_name,
                   b.display_name AS assignee_name,
                   (SELECT COUNT(*) FROM task_attachments ta WHERE ta.task_id=t.id) AS attachment_count,
                   EXISTS(SELECT 1 FROM task_favorites tf WHERE tf.task_id=t.id AND tf.user_id=%s) AS is_favorite
              FROM tasks t
              LEFT JOIN users a ON a.id = t.author_id
              LEFT JOIN users b ON b.id = t.current_assignee_id
            {where_sql}
             ORDER BY t.{sort_by} {sort_dir}
             LIMIT %s OFFSET %s
        """, [uid] + params + [page_size, offset])
        rows = cursor.fetchall()
        cursor.close()

    return {
        "items": [_format_task(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/", status_code=201)
def create_task(body: TaskCreate, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    priority = body.priority if body.priority in VALID_PRIORITIES else "normal"

    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO tasks (title, description, author_id, current_assignee_id, priority, due_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        """, (body.title, body.content, uid, body.assignee_id, priority, body.due_date or None))
        conn.commit()
        task_id = cursor.lastrowid

        if body.assignee_id != uid:
            try:
                cursor.execute("""
                    INSERT INTO notifications (recipient_id, task_id, notification_type, message)
                    VALUES (%s, %s, 'assigned', %s)
                """, (body.assignee_id, task_id, f"새 업무가 배정되었습니다: {body.title}"))
                conn.commit()
            except Exception:
                pass

        row = _get_task_row(cursor, task_id, uid)
        cursor.close()
    return _format_task(row)


@router.get("/export")
def export_tasks(
    section: str = Query("assigned_to_me"),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    due_date_from: Optional[str] = Query(None),
    due_date_to: Optional[str] = Query(None),
    fmt: str = Query("xlsx"),
    current_user: dict = Depends(get_current_user),
):
    from fastapi.responses import Response
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        where = []
        params = []
        if section == "assigned_to_me":
            where.append("t.current_assignee_id=%s"); params.append(uid)
        elif section == "assigned_by_me":
            where.append("t.author_id=%s"); params.append(uid)
        else:
            where.append("(t.current_assignee_id=%s OR t.author_id=%s)"); params.extend([uid, uid])
        if status: where.append("t.status=%s"); params.append(status)
        if priority: where.append("t.priority=%s"); params.append(priority)
        if search: where.append("t.title LIKE %s"); params.append(f"%{search}%")
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        cursor.execute(f"""
            SELECT t.title, t.status, t.priority, t.progress,
                   a.display_name AS assigner, b.display_name AS assignee,
                   t.due_date, t.created_at
              FROM tasks t
              LEFT JOIN users a ON a.id=t.author_id
              LEFT JOIN users b ON b.id=t.current_assignee_id
            {where_sql} ORDER BY t.created_at DESC
        """, params)
        rows = cursor.fetchall()
        cursor.close()

    def _csv_field(val) -> str:
        """CSV 필드 이스케이프: 포뮬러 인젝션 방지 + 쉼표/따옴표 처리"""
        s = str(val) if val is not None else ""
        # Excel/LibreOffice 포뮬러 인젝션 방지 (=, +, -, @ 로 시작하는 값)
        if s and s[0] in ("=", "+", "-", "@"):
            s = "'" + s
        # 쉼표·따옴표·줄바꿈 포함 시 큰따옴표로 감싸기
        if "," in s or '"' in s or "\n" in s:
            s = '"' + s.replace('"', '""') + '"'
        return s

    lines = ["업무명,상태,우선순위,진행률,지시자,담당자,마감일,등록일"]
    for r in rows:
        due = r["due_date"].strftime("%Y-%m-%d") if r.get("due_date") else ""
        cre = r["created_at"].strftime("%Y-%m-%d") if r.get("created_at") else ""
        lines.append(",".join([
            _csv_field(r["title"]),
            _csv_field(r["status"]),
            _csv_field(r["priority"]),
            f'{r["progress"]}%',
            _csv_field(r.get("assigner") or ""),
            _csv_field(r.get("assignee") or ""),
            _csv_field(due),
            _csv_field(cre),
        ]))
    content = "\n".join(lines)
    return Response(
        content=content.encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": 'attachment; filename="tasks.csv"'},
    )


@router.post("/bulk-status")
def bulk_status(body: BulkStatusRequest, current_user: dict = Depends(get_current_user)):
    if body.status not in VALID_STATUSES:
        raise HTTPException(400, detail="유효하지 않은 상태입니다.")
    if body.status == "rejected" and not (body.comment or "").strip():
        raise HTTPException(400, detail="반려 시 코멘트는 필수입니다.")
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        for tid in body.task_ids:
            cursor.execute("UPDATE tasks SET status=%s WHERE id=%s", (body.status, tid))
            if body.comment:
                cursor.execute("""
                    INSERT INTO task_comments (task_id, author_id, content) VALUES (%s,%s,%s)
                """, (tid, uid, f"[일괄처리] {body.comment}"))
        conn.commit()
        cursor.close()
    return {"message": f"{len(body.task_ids)}건 처리 완료"}


def _guess_mime(filename: str) -> str:
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    return {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
        "svg": "image/svg+xml", "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "zip": "application/zip", "txt": "text/plain",
    }.get(ext, "application/octet-stream")


@router.get("/{task_id}")
def get_task(task_id: int, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        row = _get_task_row(cursor, task_id, uid)
        if not row:
            cursor.close()
            raise HTTPException(404, detail="업무를 찾을 수 없습니다.")
        task = _format_task(row)

        cursor.execute("""
            SELECT id, filename, file_size, uploader_id, created_at
              FROM task_attachments WHERE task_id = %s ORDER BY created_at ASC
        """, (task_id,))
        task["attachments"] = [
            {
                "id": a["id"],
                "filename": a["filename"],
                "file_size": a["file_size"],
                "mime_type": _guess_mime(a["filename"]),
                "uploader_id": a["uploader_id"],
                "created_at": a["created_at"].isoformat() if a.get("created_at") else None,
            }
            for a in cursor.fetchall()
        ]
        cursor.close()
    return task


@router.patch("/{task_id}")
def patch_task(task_id: int, body: TaskPatch, current_user: dict = Depends(get_current_user)):
    updates = {}
    if body.progress is not None: updates["progress"] = max(0, min(100, body.progress))
    if body.title is not None: updates["title"] = body.title
    if body.description is not None: updates["description"] = body.description
    if body.priority is not None and body.priority in VALID_PRIORITIES: updates["priority"] = body.priority
    if body.due_date is not None: updates["due_date"] = body.due_date or None
    if body.assignee_id is not None: updates["current_assignee_id"] = body.assignee_id
    if not updates:
        raise HTTPException(400, detail="변경할 내용이 없습니다.")
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        set_sql = ", ".join(f"{k}=%s" for k in updates)
        cursor.execute(f"UPDATE tasks SET {set_sql} WHERE id=%s", list(updates.values()) + [task_id])
        conn.commit()
        row = _get_task_row(cursor, task_id, uid)
        cursor.close()
    return _format_task(row)


@router.post("/{task_id}/status")
def update_status(task_id: int, body: StatusUpdate, current_user: dict = Depends(get_current_user)):
    if body.status not in VALID_STATUSES:
        raise HTTPException(400, detail="유효하지 않은 상태입니다.")
    if body.status == "rejected" and not (body.comment or "").strip():
        raise HTTPException(400, detail="반려 시 코멘트는 필수입니다.")
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, status, current_assignee_id, author_id, title FROM tasks WHERE id=%s", (task_id,))
        task = cursor.fetchone()
        if not task:
            cursor.close(); raise HTTPException(404, detail="업무를 찾을 수 없습니다.")

        old_status = task["status"]
        cursor.execute("UPDATE tasks SET status=%s WHERE id=%s", (body.status, task_id))
        if body.comment:
            cursor.execute("INSERT INTO task_comments (task_id, author_id, content) VALUES (%s,%s,%s)",
                           (task_id, uid, body.comment))
        try:
            cursor.execute("""
                INSERT INTO task_history (task_id, actor_id, action_type, old_status, new_status)
                VALUES (%s,%s,'status_change',%s,%s)
            """, (task_id, uid, old_status, body.status))
        except Exception:
            pass

        notify_id = task["author_id"] if uid == task["current_assignee_id"] else task["current_assignee_id"]
        if notify_id and notify_id != uid:
            labels = {"pending":"대기","in_progress":"진행중","review":"검토요청","approved":"완료","rejected":"반려"}
            try:
                cursor.execute("""
                    INSERT INTO notifications (recipient_id, task_id, notification_type, message)
                    VALUES (%s,%s,'status_changed',%s)
                """, (notify_id, task_id, f"업무 상태 변경: {task['title']} → {labels.get(body.status, body.status)}"))
            except Exception:
                pass

        conn.commit()
        row = _get_task_row(cursor, task_id, uid)
        cursor.close()
    return {"message": "상태가 변경되었습니다.", "task": _format_task(row)}


@router.post("/{task_id}/favorite")
def toggle_favorite(task_id: int, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT 1 FROM task_favorites WHERE user_id=%s AND task_id=%s", (uid, task_id))
        exists = cursor.fetchone()
        if exists:
            cursor.execute("DELETE FROM task_favorites WHERE user_id=%s AND task_id=%s", (uid, task_id))
            is_favorite = False
        else:
            cursor.execute("INSERT INTO task_favorites (user_id, task_id) VALUES (%s,%s)", (uid, task_id))
            is_favorite = True
        conn.commit()
        cursor.close()
    return {"is_favorite": is_favorite}


@router.get("/{task_id}/logs")
def get_logs(task_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.id, c.content, c.created_at,
                   u.display_name AS author_name, u.id AS author_id
              FROM task_comments c
              JOIN users u ON u.id = c.author_id
             WHERE c.task_id = %s
             ORDER BY c.created_at ASC
        """, (task_id,))
        comments = cursor.fetchall()

        history_rows = []
        try:
            cursor.execute("""
                SELECT h.id, h.action_type, h.old_status, h.new_status, h.note, h.created_at,
                       u.id AS actor_id, u.display_name AS actor_name
                  FROM task_history h
                  JOIN users u ON u.id = h.actor_id
                 WHERE h.task_id = %s
                 ORDER BY h.created_at ASC
            """, (task_id,))
            history_rows = cursor.fetchall()
        except Exception:
            pass
        cursor.close()

    result = []
    for r in comments:
        result.append({
            "id": r["id"],
            "action": "comment",
            "comment": r["content"],
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
            "user": {"id": r["author_id"], "name": r["author_name"]},
            "old_value": None,
            "new_value": None,
        })
    for h in history_rows:
        action_map = {
            "status_change": "status_changed",
            "status_changed": "status_changed",
            "reassigned": "reassigned",
            "created": "created",
            "updated": "updated",
        }
        result.append({
            "id": f"h_{h['id']}",
            "action": action_map.get(h["action_type"], h["action_type"]),
            "comment": h.get("note"),
            "created_at": h["created_at"].isoformat() if h.get("created_at") else None,
            "user": {"id": h["actor_id"], "name": h["actor_name"]},
            "old_value": h.get("old_status"),
            "new_value": h.get("new_status"),
        })
    result.sort(key=lambda x: x["created_at"] or "")
    return result


@router.post("/{task_id}/comment")
def add_comment(task_id: int, body: dict, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    comment = (body.get("comment") or "").strip()
    if not comment:
        raise HTTPException(400, detail="댓글 내용을 입력해주세요.")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO task_comments (task_id, author_id, content) VALUES (%s,%s,%s)",
                       (task_id, uid, comment))
        conn.commit()
        cursor.close()
    return {"ok": True}


@router.patch("/{task_id}/comments/{comment_id}")
def edit_comment(task_id: int, comment_id: int, body: dict, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    comment = (body.get("comment") or "").strip()
    if not comment:
        raise HTTPException(400, detail="댓글 내용을 입력해주세요.")
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT author_id FROM task_comments WHERE id=%s AND task_id=%s", (comment_id, task_id))
        row = cursor.fetchone()
        if not row:
            cursor.close(); raise HTTPException(404, detail="댓글을 찾을 수 없습니다.")
        if row["author_id"] != uid:
            cursor.close(); raise HTTPException(403, detail="본인의 댓글만 수정할 수 있습니다.")
        cursor.execute("UPDATE task_comments SET content=%s WHERE id=%s", (comment, comment_id))
        conn.commit()
        cursor.close()
    return {"ok": True}


@router.delete("/{task_id}/comments/{comment_id}", status_code=204)
def delete_comment(task_id: int, comment_id: int, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT author_id FROM task_comments WHERE id=%s AND task_id=%s", (comment_id, task_id))
        row = cursor.fetchone()
        if not row:
            cursor.close(); raise HTTPException(404, detail="댓글을 찾을 수 없습니다.")
        if row["author_id"] != uid:
            cursor.close(); raise HTTPException(403, detail="본인의 댓글만 삭제할 수 있습니다.")
        cursor.execute("DELETE FROM task_comments WHERE id=%s", (comment_id,))
        conn.commit()
        cursor.close()


@router.post("/{task_id}/reassign")
def reassign_task(task_id: int, body: ReassignRequest, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT title FROM tasks WHERE id=%s", (task_id,))
        task = cursor.fetchone()
        if not task:
            cursor.close(); raise HTTPException(404, detail="업무를 찾을 수 없습니다.")
        cursor.execute("UPDATE tasks SET current_assignee_id=%s WHERE id=%s", (body.assignee_id, task_id))
        if body.assignee_id != uid:
            try:
                cursor.execute("""
                    INSERT INTO notifications (recipient_id, task_id, notification_type, message)
                    VALUES (%s,%s,'reassigned',%s)
                """, (body.assignee_id, task_id, f"업무 담당자로 지정되었습니다: {task['title']}"))
            except Exception:
                pass
        conn.commit()
        row = _get_task_row(cursor, task_id, uid)
        cursor.close()
    return _format_task(row)


@router.post("/{task_id}/clone")
def clone_task(task_id: int, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE id=%s", (task_id,))
        original = cursor.fetchone()
        if not original:
            cursor.close(); raise HTTPException(404, detail="업무를 찾을 수 없습니다.")
        cursor.execute("""
            INSERT INTO tasks (title, description, author_id, current_assignee_id, priority, due_date, status)
            VALUES (%s,%s,%s,%s,%s,%s,'pending')
        """, (f"[복사] {original['title']}", original["description"], uid,
              original["current_assignee_id"], original["priority"], original["due_date"]))
        conn.commit()
        new_id = cursor.lastrowid
        row = _get_task_row(cursor, new_id, uid)
        cursor.close()
    return _format_task(row)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tasks WHERE id=%s", (task_id,))
        if not cursor.fetchone():
            cursor.close(); raise HTTPException(404, detail="업무를 찾을 수 없습니다.")
        cursor.execute("DELETE FROM task_favorites WHERE task_id=%s", (task_id,))
        cursor.execute("DELETE FROM task_comments WHERE task_id=%s", (task_id,))
        cursor.execute("DELETE FROM task_attachments WHERE task_id=%s", (task_id,))
        cursor.execute("DELETE FROM notifications WHERE task_id=%s", (task_id,))
        cursor.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
        conn.commit()
        cursor.close()
