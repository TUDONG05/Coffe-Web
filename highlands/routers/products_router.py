"""
Products endpoints: GET /api/products, GET /api/products/{id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
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
    image_url: Optional[str]
    video_url: Optional[str]
    avg_rating: float = 0.0
    review_count: int = 0

    class Config:
        from_attributes = True


def _with_ratings(products: list, db: Session) -> list[dict]:
    if not products:
        return []
    ids = [p.id for p in products]
    rows = db.query(
        models.ProductReview.product_id,
        func.avg(models.ProductReview.stars).label("avg"),
        func.count(models.ProductReview.id).label("cnt"),
    ).filter(models.ProductReview.product_id.in_(ids)).group_by(models.ProductReview.product_id).all()
    stats = {r.product_id: (round(float(r.avg), 1), r.cnt) for r in rows}
    result = []
    for p in products:
        avg, cnt = stats.get(p.id, (0.0, 0))
        d = {c.name: getattr(p, c.name) for c in p.__table__.columns}
        d["avg_rating"] = avg
        d["review_count"] = cnt
        result.append(d)
    return result


@router.get("")
def list_products(
    category: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Product).filter(models.Product.is_active == 1)
    if category:
        query = query.filter(models.Product.category == category)
    if q:
        keyword = f"%{q}%"
        query = query.filter(
            or_(models.Product.name.ilike(keyword), models.Product.category.ilike(keyword))
        )
    return _with_ratings(query.all(), db)


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return _with_ratings([p], db)[0]
