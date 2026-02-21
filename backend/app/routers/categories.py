from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.task import Category, Tag
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/categories", tags=["categories"])


class CategoryCreate(BaseModel):
    name: str
    color: str = "#6366f1"


@router.get("/")
def list_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    cats = db.query(Category).all()
    return [{"id": c.id, "name": c.name, "color": c.color} for c in cats]


@router.post("/", status_code=201)
def create_category(req: CategoryCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if db.query(Category).filter(Category.name == req.name).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 카테고리입니다.")
    cat = Category(name=req.name, color=req.color)
    db.add(cat)
    db.commit()
    return {"id": cat.id, "name": cat.name, "color": cat.color}


@router.get("/tags")
def list_tags(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tags = db.query(Tag).all()
    return [{"id": t.id, "name": t.name} for t in tags]
