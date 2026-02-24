from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from ..auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/api/bug-reports", tags=["bug-reports"])


class BugReportCreate(BaseModel):
    title: str
    description: str
    page: Optional[str] = None       # 어느 페이지에서 발생했는지
    steps: Optional[str] = None      # 재현 단계
    severity: str = "normal"         # low / normal / high / critical


@router.post("/", status_code=201)
def create_bug_report(body: BugReportCreate, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        # 테이블 없으면 자동 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bug_reports (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                reporter_id BIGINT UNSIGNED NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                page VARCHAR(100),
                steps TEXT,
                severity ENUM('low','normal','high','critical') DEFAULT 'normal',
                status ENUM('open','in_review','resolved','closed') DEFAULT 'open',
                admin_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            """INSERT INTO bug_reports (reporter_id, title, description, page, steps, severity)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (uid, body.title, body.description, body.page, body.steps, body.severity),
        )
        conn.commit()
        report_id = cursor.lastrowid
        cursor.close()
    return {"id": report_id, "message": "오류가 접수됐습니다. 감사합니다."}


@router.get("/")
def list_bug_reports(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        # 관리자 여부 확인
        cursor.execute("SELECT role FROM users WHERE id=%s", (uid,))
        user_row = cursor.fetchone()
        is_admin = user_row and user_row["role"] == "admin"

        # 테이블 없으면 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bug_reports (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                reporter_id BIGINT UNSIGNED NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                page VARCHAR(100),
                steps TEXT,
                severity ENUM('low','normal','high','critical') DEFAULT 'normal',
                status ENUM('open','in_review','resolved','closed') DEFAULT 'open',
                admin_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        conditions = []
        params = []

        if not is_admin:
            conditions.append("br.reporter_id = %s")
            params.append(uid)
        if status:
            conditions.append("br.status = %s")
            params.append(status)
        if severity:
            conditions.append("br.severity = %s")
            params.append(severity)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        cursor.execute(
            f"SELECT COUNT(*) AS cnt FROM bug_reports br {where}", params
        )
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * page_size
        cursor.execute(
            f"""SELECT br.id, br.title, br.description, br.page, br.steps,
                       br.severity, br.status, br.admin_note,
                       br.created_at, br.updated_at,
                       u.display_name AS reporter_name, u.department AS reporter_dept
                FROM bug_reports br
                JOIN users u ON u.id = br.reporter_id
                {where}
                ORDER BY br.created_at DESC
                LIMIT %s OFFSET %s""",
            params + [page_size, offset],
        )
        rows = cursor.fetchall()
        cursor.close()

    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "title": r["title"],
            "description": r["description"],
            "page": r["page"],
            "steps": r["steps"],
            "severity": r["severity"],
            "status": r["status"],
            "admin_note": r["admin_note"],
            "reporter_name": r["reporter_name"],
            "reporter_dept": r["reporter_dept"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
        })
    return {"total": total, "items": items}


@router.patch("/{report_id}")
def update_bug_report(
    report_id: int,
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT role FROM users WHERE id=%s", (uid,))
        user_row = cursor.fetchone()
        is_admin = user_row and user_row["role"] == "admin"
        if not is_admin:
            from fastapi import HTTPException
            raise HTTPException(403, detail="관리자만 수정할 수 있습니다.")

        fields = []
        params = []
        if "status" in body:
            fields.append("status=%s")
            params.append(body["status"])
        if "admin_note" in body:
            fields.append("admin_note=%s")
            params.append(body["admin_note"])
        if not fields:
            return {"ok": True}
        params.append(report_id)
        cursor.execute(f"UPDATE bug_reports SET {', '.join(fields)} WHERE id=%s", params)
        conn.commit()
        cursor.close()
    return {"ok": True}
