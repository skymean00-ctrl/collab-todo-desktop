import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from ..auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/api/attachments", tags=["attachments"])

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/{task_id}", status_code=201)
async def upload_attachment(
    task_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["id"]
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, detail="파일 크기는 50MB를 초과할 수 없습니다.")

    ext = os.path.splitext(file.filename or "")[1]
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "INSERT INTO task_attachments (task_id, uploader_id, filename, stored_filename, file_size) VALUES (%s,%s,%s,%s,%s)",
            (task_id, uid, file.filename, stored_filename, len(content)),
        )
        conn.commit()
        attachment_id = cursor.lastrowid
        cursor.close()

    return {
        "id": attachment_id,
        "filename": file.filename,
        "file_size": len(content),
        "mime_type": file.content_type or "application/octet-stream",
    }


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    current_user: dict = Depends(get_current_user),
):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT filename, stored_filename FROM task_attachments WHERE id=%s",
            (attachment_id,),
        )
        row = cursor.fetchone()
        cursor.close()

    if not row:
        raise HTTPException(404, detail="파일을 찾을 수 없습니다.")

    file_path = os.path.join(UPLOAD_DIR, row["stored_filename"])
    if not os.path.exists(file_path):
        raise HTTPException(404, detail="파일이 서버에 존재하지 않습니다.")

    return FileResponse(
        path=file_path,
        filename=row["filename"],
        media_type="application/octet-stream",
    )


@router.delete("/{attachment_id}", status_code=204)
def delete_attachment(
    attachment_id: int,
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["id"]
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT uploader_id, stored_filename FROM task_attachments WHERE id=%s",
            (attachment_id,),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            raise HTTPException(404, detail="파일을 찾을 수 없습니다.")

        if row["uploader_id"] != uid:
            cursor.execute("SELECT role FROM users WHERE id=%s", (uid,))
            user_row = cursor.fetchone()
            if not user_row or user_row["role"] != "admin":
                cursor.close()
                raise HTTPException(403, detail="파일을 삭제할 권한이 없습니다.")

        cursor.execute("DELETE FROM task_attachments WHERE id=%s", (attachment_id,))
        conn.commit()
        stored_filename = row["stored_filename"]
        cursor.close()

    file_path = os.path.join(UPLOAD_DIR, stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
