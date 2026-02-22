from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.task import Category, Tag
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/categories", tags=["categories"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    return current_user


class CategoryCreate(BaseModel):
    name: str
    color: str = "#6366f1"


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


@router.get("/")
def list_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    cats = db.query(Category).order_by(Category.name).all()
    return [{"id": c.id, "name": c.name, "color": c.color} for c in cats]


@router.post("/", status_code=201)
def create_category(
    req: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="카테고리 이름을 입력해주세요.")
    if db.query(Category).filter(Category.name == name).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 카테고리입니다.")
    cat = Category(name=name, color=req.color)
    db.add(cat)
    db.commit()
    return {"id": cat.id, "name": cat.name, "color": cat.color}


@router.patch("/{category_id}")
def update_category(
    category_id: int,
    req: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")
    if req.name is not None:
        name = req.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="카테고리 이름을 입력해주세요.")
        existing = db.query(Category).filter(Category.name == name, Category.id != category_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 카테고리 이름입니다.")
        cat.name = name
    if req.color is not None:
        cat.color = req.color
    db.commit()
    return {"id": cat.id, "name": cat.name, "color": cat.color}


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")
    # 해당 카테고리를 사용 중인 업무들은 category_id를 NULL로 처리
    from app.models.task import Task
    db.query(Task).filter(Task.category_id == category_id).update({"category_id": None})
    db.delete(cat)
    db.commit()


@router.get("/tags")
def list_tags(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tags = db.query(Tag).order_by(Tag.name).all()
    return [{"id": t.id, "name": t.name} for t in tags]


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="태그를 찾을 수 없습니다.")
    db.delete(tag)
    db.commit()
