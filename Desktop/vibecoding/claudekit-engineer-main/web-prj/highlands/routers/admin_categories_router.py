"""
Admin endpoints for category management: CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import require_admin

router = APIRouter(prefix="/api/admin/categories", tags=["admin-categories"])


# ── Schemas ────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    emoji: str = "☕"


class CategoryUpdate(BaseModel):
    name: str | None = None
    emoji: str | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    emoji: str
    is_active: int

    class Config:
        from_attributes = True


# ── Routes ─────────────────────────────────────────────────

@router.get("", response_model=list[CategoryOut])
def list_categories(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all categories."""
    categories = db.query(models.Category).all()
    return categories


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(
    body: CategoryCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new category."""
    existing = db.query(models.Category).filter(models.Category.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên danh mục đã tồn tại")

    category = models.Category(
        name=body.name,
        emoji=body.emoji,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get category details."""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Danh mục không tồn tại")
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    body: CategoryUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update category details."""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Danh mục không tồn tại")

    if body.name is not None:
        existing = db.query(models.Category).filter(
            models.Category.name == body.name,
            models.Category.id != category_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Tên danh mục đã tồn tại")
        category.name = body.name

    if body.emoji is not None:
        category.emoji = body.emoji

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a category (soft delete)."""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Danh mục không tồn tại")

    category.is_active = 0
    db.commit()
    return {"success": True, "message": "Danh mục đã được xóa"}
