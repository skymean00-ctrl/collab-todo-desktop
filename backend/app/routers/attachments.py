import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.task import Task, Attachment
from app.utils.auth import get_current_user
from app.config import get_settings
import aiofiles

router = APIRouter(prefix="/api/attachments", tags=["attachments"])
settings = get_settings()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

ALLOWED_EXTENSIONS = {
    # 문서
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".hwp", ".hwpx",
    # 텍스트
    ".txt", ".csv", ".md",
    # 이미지
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg",
    # 압축
    ".zip", ".7z", ".tar", ".gz",
    # 기타
    ".xml", ".json",
}


@router.post("/{task_id}")
async def upload_file(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="업무를 찾을 수 없습니다.")

    os.makedirs(settings.file_storage_path, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"허용되지 않는 파일 형식입니다. ({ext or '확장자 없음'})")

    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.file_storage_path, stored_name)

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기는 50MB를 초과할 수 없습니다.")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    attachment = Attachment(
        task_id=task_id,
        uploader_id=current_user.id,
        filename=file.filename,
        stored_name=stored_name,
        file_size=len(content),
        mime_type=file.content_type,
    )
    db.add(attachment)
    db.commit()

    return {
        "id": attachment.id,
        "filename": attachment.filename,
        "file_size": attachment.file_size,
        "mime_type": attachment.mime_type,
        "uploaded_at": attachment.uploaded_at.isoformat(),
    }


@router.get("/{attachment_id}/download")
def download_file(
    attachment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    file_path = os.path.join(settings.file_storage_path, attachment.stored_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일이 서버에 존재하지 않습니다.")

    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.mime_type or "application/octet-stream",
    )


@router.delete("/{attachment_id}")
def delete_file(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    if attachment.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="파일을 삭제할 권한이 없습니다.")

    file_path = os.path.join(settings.file_storage_path, attachment.stored_name)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(attachment)
    db.commit()
    return {"message": "파일이 삭제되었습니다."}
