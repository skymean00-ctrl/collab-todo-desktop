from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user, hash_password
from ..db import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    department_name: Optional[str] = None


class FilterPresetCreate(BaseModel):
    name: str
    section: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    sort_by: Optional[str] = None
    sort_dir: Optional[str] = None
    due_date_from: Optional[str] = None
    due_date_to: Optional[str] = None


class NotifPrefUpdate(BaseModel):
    notify_assigned: Optional[bool] = None
    notify_status_changed: Optional[bool] = None
    notify_due_soon: Optional[bool] = None
    notify_mentioned: Optional[bool] = None
    notify_reassigned: Optional[bool] = None
    notify_commented: Optional[bool] = None
    email_assigned: Optional[bool] = None
    email_status_changed: Optional[bool] = None
    email_due_soon: Optional[bool] = None
    email_mentioned: Optional[bool] = None
    email_reassigned: Optional[bool] = None


class AdminCreateUser(BaseModel):
    username: str
    name: str
    email: str
    password: str
    department_name: str = ""
    role: str = "user"


class AdminUpdateUser(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    department_name: Optional[str] = None


# ── 사용자 목록 ────────────────────────────────────────────────

@router.get("/")
def list_users(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, display_name, email, role, department FROM users WHERE is_active=1 AND is_deleted=0 ORDER BY display_name")
        users = cursor.fetchall()
        cursor.close()
    return [{"id": u["id"], "username": u["username"], "name": u["display_name"],
             "email": u["email"], "role": u["role"], "department": u["department"] or ""} for u in users]


@router.get("/departments/list")
def list_departments():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM departments ORDER BY name")
        rows = cursor.fetchall()
        cursor.close()
    return [r[0] for r in rows]


# ── 내 정보 ────────────────────────────────────────────────────

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, display_name, email, role, department FROM users WHERE id=%s", (uid,))
        user = cursor.fetchone()
        cursor.close()
    if not user:
        raise HTTPException(404)
    return {"id": user["id"], "username": user["username"], "name": user["display_name"],
            "email": user["email"], "role": user["role"], "department": user["department"] or "",
            "is_admin": user["role"] == "admin", "is_verified": True}


@router.patch("/me")
def update_me(body: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    updates = {}
    if body.name: updates["display_name"] = body.name.strip()
    if body.department_name is not None: updates["department"] = body.department_name
    if not updates:
        raise HTTPException(400, detail="변경할 내용이 없습니다.")
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        set_sql = ", ".join(f"{k}=%s" for k in updates)
        cursor.execute(f"UPDATE users SET {set_sql} WHERE id=%s", list(updates.values()) + [uid])
        conn.commit()
        cursor.execute("SELECT id, display_name, email, role, department FROM users WHERE id=%s", (uid,))
        user = cursor.fetchone()
        cursor.close()
    return {"id": user["id"], "name": user["display_name"], "email": user["email"],
            "department": user["department"] or ""}


# ── 필터 프리셋 ────────────────────────────────────────────────

@router.get("/me/filter-presets")
def get_presets(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM filter_presets WHERE user_id=%s ORDER BY created_at DESC", (uid,))
        rows = cursor.fetchall()
        cursor.close()
    return rows


@router.post("/me/filter-presets", status_code=201)
def create_preset(body: FilterPresetCreate, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO filter_presets (user_id, name, section, status, priority, sort_by, sort_dir, due_date_from, due_date_to)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (uid, body.name, body.section, body.status, body.priority,
              body.sort_by, body.sort_dir, body.due_date_from, body.due_date_to))
        conn.commit()
        cursor.execute("SELECT * FROM filter_presets WHERE id=%s", (cursor.lastrowid,))
        row = cursor.fetchone()
        cursor.close()
    return row


@router.delete("/me/filter-presets/{preset_id}", status_code=204)
def delete_preset(preset_id: int, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM filter_presets WHERE id=%s AND user_id=%s", (preset_id, uid))
        conn.commit()
        cursor.close()


# ── 알림 설정 ────────────────────────────────────────────────

@router.get("/me/notification-preferences")
def get_notif_prefs(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM notification_preferences WHERE user_id=%s", (uid,))
        row = cursor.fetchone()
        cursor.close()
    if not row:
        return {k: True for k in ["notify_assigned","notify_status_changed","notify_due_soon",
                                   "notify_mentioned","notify_reassigned","notify_commented",
                                   "email_assigned","email_status_changed","email_due_soon",
                                   "email_mentioned","email_reassigned"]}
    return {k: bool(v) for k, v in row.items() if k != "user_id"}


@router.patch("/me/notification-preferences")
def update_notif_prefs(body: NotifPrefUpdate, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id FROM notification_preferences WHERE user_id=%s", (uid,))
        exists = cursor.fetchone()
        if exists and data:
            set_sql = ", ".join(f"{k}=%s" for k in data)
            cursor.execute(f"UPDATE notification_preferences SET {set_sql} WHERE user_id=%s",
                           list(data.values()) + [uid])
        elif not exists:
            cols = ["user_id"] + list(data.keys())
            vals = [uid] + list(data.values())
            cursor.execute(f"INSERT INTO notification_preferences ({','.join(cols)}) VALUES ({','.join(['%s']*len(vals))})", vals)
        conn.commit()
        cursor.execute("SELECT * FROM notification_preferences WHERE user_id=%s", (uid,))
        row = cursor.fetchone()
        cursor.close()
    if not row:
        return {"ok": True}
    return {k: bool(v) for k, v in row.items() if k != "user_id"}


# ── 관리자 전용 ────────────────────────────────────────────────

def _require_admin(current_user: dict):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT role FROM users WHERE id=%s", (current_user["id"],))
        user = cursor.fetchone()
        cursor.close()
    if not user or user["role"] != "admin":
        raise HTTPException(403, detail="관리자 권한이 필요합니다.")


# 사용자 목록 (관리자용)
@router.get("/admin/all")
def admin_list_users(current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, display_name, email, role, department, is_active, created_at "
            "FROM users WHERE is_deleted=0 ORDER BY created_at DESC"
        )
        users = cursor.fetchall()
        cursor.close()
    return [{
        "id": u["id"],
        "username": u["username"],
        "name": u["display_name"],
        "email": u["email"],
        "role": u["role"],
        "is_admin": u["role"] == "admin",
        "department": u["department"] or "",
        "is_active": bool(u["is_active"]),
        "created_at": u["created_at"].isoformat() if u.get("created_at") else None,
    } for u in users]


# 사용자 생성 (관리자용)
@router.post("/admin/create", status_code=201)
def admin_create_user(body: AdminCreateUser, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    if not body.username.strip():
        raise HTTPException(400, detail="아이디를 입력해주세요.")
    if not body.name.strip():
        raise HTTPException(400, detail="이름을 입력해주세요.")
    if len(body.password) < 6:
        raise HTTPException(400, detail="비밀번호는 6자 이상이어야 합니다.")
    role = body.role if body.role in ("user", "admin") else "user"
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM users WHERE username=%s OR (email != '' AND email=%s)",
            (body.username.strip(), body.email.strip())
        )
        if cursor.fetchone():
            cursor.close()
            raise HTTPException(409, detail="이미 사용 중인 아이디 또는 이메일입니다.")
        cursor.execute(
            "INSERT INTO users (username, display_name, email, password_hash, department, role, is_active) "
            "VALUES (%s,%s,%s,%s,%s,%s,1)",
            (body.username.strip(), body.name.strip(), body.email.strip(),
             hash_password(body.password), body.department_name, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
    return {"ok": True, "id": user_id}


# 사용자 수정 (관리자용)
@router.patch("/admin/{user_id}")
def admin_update_user(user_id: int, body: AdminUpdateUser, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    updates = {}
    if body.name is not None: updates["display_name"] = body.name.strip()
    if body.email is not None: updates["email"] = body.email.strip()
    if body.role is not None and body.role in ("user", "admin"): updates["role"] = body.role
    if body.is_active is not None: updates["is_active"] = int(body.is_active)
    if body.department_name is not None: updates["department"] = body.department_name
    if not updates:
        raise HTTPException(400, detail="변경할 내용이 없습니다.")
    with get_db() as conn:
        cursor = conn.cursor()
        set_sql = ", ".join(f"{k}=%s" for k in updates)
        cursor.execute(f"UPDATE users SET {set_sql} WHERE id=%s", list(updates.values()) + [user_id])
        conn.commit()
        cursor.close()
    return {"ok": True}


# 비밀번호 초기화 (관리자용)
@router.post("/admin/{user_id}/reset-password")
def admin_reset_password(user_id: int, body: dict, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    new_pw = (body.get("new_password") or "").strip()
    if len(new_pw) < 6:
        raise HTTPException(400, detail="비밀번호는 6자 이상이어야 합니다.")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash=%s WHERE id=%s", (hash_password(new_pw), user_id))
        conn.commit()
        cursor.close()
    return {"ok": True, "message": "비밀번호가 초기화되었습니다.", "temp_password": new_pw}


# 사용자 삭제 (관리자용 - 소프트 삭제: 기록 보존, 로그인·목록에서만 제외)
@router.delete("/admin/{user_id}")
def admin_delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    if user_id == current_user["id"]:
        raise HTTPException(400, detail="자신의 계정은 삭제할 수 없습니다.")
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE id=%s AND is_deleted=0", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(404, detail="사용자를 찾을 수 없습니다.")
        # 소프트 삭제: 업무/이력/댓글 등 기록은 모두 보존
        # is_deleted=1: 로그인 불가, 사용자 목록에서 제외
        cursor.execute(
            "UPDATE users SET is_deleted=1, is_active=0 WHERE id=%s",
            (user_id,)
        )
        conn.commit()
        cursor.close()
    return {"ok": True}


# 통계 (관리자용)
@router.get("/admin/stats")
def admin_stats(current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    from datetime import date
    today = date.today().isoformat()
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE is_active=1")
        total_users = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM tasks")
        total_tasks = cursor.fetchone()["total"]
        cursor.execute(
            "SELECT COUNT(*) AS total FROM tasks WHERE due_date < %s AND status NOT IN ('approved','rejected')",
            (today,)
        )
        overdue = cursor.fetchone()["total"]
        cursor.execute("SELECT status, COUNT(*) AS cnt FROM tasks GROUP BY status")
        status_breakdown = {r["status"]: r["cnt"] for r in cursor.fetchall()}
        cursor.execute("""
            SELECT u.department, COUNT(t.id) AS task_count
            FROM users u LEFT JOIN tasks t ON t.current_assignee_id = u.id
            WHERE u.is_active=1
            GROUP BY u.department ORDER BY task_count DESC
        """)
        dept_stats = [{"department": r["department"] or "미지정", "task_count": r["task_count"]}
                      for r in cursor.fetchall()]
        cursor.execute("""
            SELECT u.id AS user_id, u.display_name AS name, COUNT(t.id) AS pending_tasks
            FROM users u LEFT JOIN tasks t ON t.current_assignee_id=u.id AND t.status NOT IN ('approved','rejected')
            WHERE u.is_active=1
            GROUP BY u.id, u.display_name
            ORDER BY pending_tasks DESC LIMIT 10
        """)
        top_assignees = [{"user_id": r["user_id"], "name": r["name"], "pending_tasks": r["pending_tasks"]}
                         for r in cursor.fetchall()]
        cursor.close()
    return {
        "total_users": total_users,
        "total_tasks": total_tasks,
        "overdue": overdue,
        "status_breakdown": status_breakdown,
        "dept_stats": dept_stats,
        "top_assignees": top_assignees,
    }


# 부서 목록 (관리자용)
@router.get("/admin/departments")
def admin_list_departments(current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.id, d.name, COUNT(u.id) AS user_count
            FROM departments d LEFT JOIN users u ON u.department=d.name AND u.is_active=1
            GROUP BY d.id, d.name ORDER BY d.name
        """)
        depts = cursor.fetchall()
        cursor.close()
    return depts


# 부서 추가
@router.post("/admin/departments")
def admin_add_department(body: dict, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(400, detail="부서명을 입력해주세요.")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT IGNORE INTO departments (name) VALUES (%s)", (name,))
        conn.commit()
        cursor.close()
    return {"ok": True}


# 부서 수정
@router.patch("/admin/departments/{dept_id}")
def admin_update_department(dept_id: int, body: dict, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(400, detail="부서명을 입력해주세요.")
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name FROM departments WHERE id=%s", (dept_id,))
        old = cursor.fetchone()
        if not old:
            cursor.close()
            raise HTTPException(404, detail="부서를 찾을 수 없습니다.")
        old_name = old["name"]
        cursor.execute("UPDATE departments SET name=%s WHERE id=%s", (name, dept_id))
        cursor.execute("UPDATE users SET department=%s WHERE department=%s", (name, old_name))
        conn.commit()
        cursor.close()
    return {"ok": True}


# 부서 삭제
@router.delete("/admin/departments/{dept_id}")
def admin_delete_department(dept_id: int, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM departments WHERE id=%s", (dept_id,))
        conn.commit()
        cursor.close()
    return {"ok": True}


# 공지 발송 (관리자용)
@router.post("/admin/announcement")
def admin_announcement(body: dict, current_user: dict = Depends(get_current_user)):
    _require_admin(current_user)
    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(400, detail="공지 내용을 입력해주세요.")
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE is_active=1")
        user_ids = [r["id"] for r in cursor.fetchall()]
        for uid in user_ids:
            cursor.execute(
                "INSERT INTO notifications (recipient_id, notification_type, message) VALUES (%s,'announcement',%s)",
                (uid, message)
            )
        conn.commit()
        cursor.close()
    return {"ok": True, "message": f"전체 {len(user_ids)}명에게 공지를 발송했습니다.", "sent_to": len(user_ids)}
