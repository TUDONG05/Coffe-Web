"""
Promotions endpoints:
  GET /api/promotions  — list all active promotions
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from highlands.database import get_db
from highlands import models

router = APIRouter(prefix="/api/promotions", tags=["promotions"])


class PromotionOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    discount: Optional[str]
    emoji: Optional[str]
    tag: Optional[str]
    valid_until: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=list[PromotionOut])
def list_promotions(db: Session = Depends(get_db)):
    return (
        db.query(models.Promotion)
        .filter(models.Promotion.is_active == 1)
        .order_by(models.Promotion.id)
        .all()
    )
