"""
Products endpoints: GET /api/products, GET /api/products/{id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from highlands.database import get_db
from highlands import models

router = APIRouter(prefix="/api/products", tags=["products"])


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    price: int
    description: Optional[str]
    emoji: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=list[ProductOut])
def list_products(category: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Product).filter(models.Product.is_active == 1)
    if category:
        q = q.filter(models.Product.category == category)
    return q.all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return p
