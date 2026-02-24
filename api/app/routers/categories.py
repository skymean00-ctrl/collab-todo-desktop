from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("/")
def list_categories(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        rows = cursor.fetchall()
        cursor.close()
    return rows


@router.post("/", status_code=201)
def create_category(body: dict, current_user: dict = Depends(get_current_user)):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(400, detail="카테고리명을 입력해주세요.")
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("INSERT IGNORE INTO categories (name) VALUES (%s)", (name,))
        conn.commit()
        cursor.execute("SELECT id, name FROM categories WHERE name=%s", (name,))
        row = cursor.fetchone()
        cursor.close()
    return row


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id=%s", (category_id,))
        conn.commit()
        cursor.close()
