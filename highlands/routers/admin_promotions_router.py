"""
Admin Promotions Management endpoints:
  GET    /api/admin/promotions       — List promotions (paginated, filterable)
  POST   /api/admin/promotions       — Create promotion
  GET    /api/admin/promotions/{id}  — Get promotion details
  PUT    /api/admin/promotions/{id}  — Update promotion
  PATCH  /api/admin/promotions/{id}  — Toggle active status
  DELETE /api/admin/promotions/{id}  — Delete promotion
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import require_admin

router = APIRouter(prefix="/api/admin/promotions", tags=["admin-promotions"])


class PromotionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    discount: Optional[str] = None
    image_url: Optional[str] = None
    tag: Optional[str] = None
    valid_until: Optional[str] = None


class PromotionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    discount: Optional[str] = None
    image_url: Optional[str] = None
    tag: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: Optional[int] = None


class PromotionOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    discount: Optional[str]
    image_url: Optional[str]
    tag: Optional[str]
    valid_until: Optional[str]
    is_active: int

    class Config:
        from_attributes = True


class PaginatedPromotions(BaseModel):
    items: list[PromotionOut]
    total: int
    skip: int
    limit: int
    has_next: bool


@router.get("", response_model=PaginatedPromotions)
def list_promotions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    tag: Optional[str] = None,
    is_active: Optional[int] = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(models.Promotion)

    if search:
        query = query.filter(
            models.Promotion.title.ilike(f"%{search}%") |
            models.Promotion.description.ilike(f"%{search}%")
        )
    if tag:
        query = query.filter(models.Promotion.tag == tag)
    if is_active is not None:
        query = query.filter(models.Promotion.is_active == is_active)

    total = query.count()
    items = query.order_by(models.Promotion.id.desc()).offset(skip).limit(limit).all()

    return {"items": items, "total": total, "skip": skip, "limit": limit, "has_next": skip + limit < total}


@router.post("", response_model=PromotionOut, status_code=201)
def create_promotion(
    body: PromotionCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    promo = models.Promotion(
        title=body.title,
        description=body.description,
        discount=body.discount,
        image_url=body.image_url,
        tag=body.tag or "HOT",
        valid_until=body.valid_until,
        is_active=1,
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo


@router.get("/{promo_id}", response_model=PromotionOut)
def get_promotion(
    promo_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    promo = db.query(models.Promotion).filter(models.Promotion.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Ưu đãi không tồn tại")
    return promo


@router.put("/{promo_id}", response_model=PromotionOut)
def update_promotion(
    promo_id: int,
    body: PromotionUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    promo = db.query(models.Promotion).filter(models.Promotion.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Ưu đãi không tồn tại")

    for field in ("title", "description", "discount", "image_url", "tag", "valid_until", "is_active"):
        val = getattr(body, field)
        if val is not None:
            setattr(promo, field, val)

    db.commit()
    db.refresh(promo)
    return promo


@router.patch("/{promo_id}", response_model=PromotionOut)
def toggle_promotion(
    promo_id: int,
    body: PromotionUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    promo = db.query(models.Promotion).filter(models.Promotion.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Ưu đãi không tồn tại")

    if body.is_active is not None:
        promo.is_active = body.is_active

    db.commit()
    db.refresh(promo)
    return promo


@router.delete("/{promo_id}")
def delete_promotion(
    promo_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    promo = db.query(models.Promotion).filter(models.Promotion.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Ưu đãi không tồn tại")

    db.delete(promo)
    db.commit()
    return {"detail": "Đã xóa ưu đãi"}
