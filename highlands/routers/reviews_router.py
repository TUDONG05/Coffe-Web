"""
Reviews endpoints:
  GET  /api/reviews/product/{id}        — public: get reviews for a product
  GET  /api/reviews/can-review/{id}     — auth: check if user can review product
  POST /api/reviews                     — auth: submit a review (must have bought)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from typing import Optional
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import get_current_user, require_login

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


class ReviewIn(BaseModel):
    product_id: int
    stars: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    product_id: int
    user_id: int
    user_name: str
    stars: int
    comment: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


def _user_bought_product(db: Session, user_id: int, product_id: int) -> bool:
    """Check if user has at least one completed/confirmed order containing this product."""
    return db.query(models.OrderItem).join(models.Order).filter(
        models.Order.user_id == user_id,
        models.Order.status.in_(["done", "confirmed"]),
        models.OrderItem.product_id == product_id,
    ).first() is not None


@router.get("/product/{product_id}")
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    reviews = (
        db.query(models.ProductReview)
        .filter(models.ProductReview.product_id == product_id)
        .order_by(models.ProductReview.created_at.desc())
        .all()
    )
    avg = db.query(func.avg(models.ProductReview.stars)).filter(
        models.ProductReview.product_id == product_id
    ).scalar()

    return {
        "reviews": [
            {
                "id": r.id,
                "user_name": r.user.name if r.user else "Ẩn danh",
                "stars": r.stars,
                "comment": r.comment,
                "created_at": r.created_at.strftime("%d/%m/%Y"),
            }
            for r in reviews
        ],
        "avg_rating": round(float(avg), 1) if avg else 0,
        "count": len(reviews),
    }


@router.get("/can-review/{product_id}")
def can_review(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    if not current_user:
        return {"can_review": False, "reason": "not_logged_in"}

    already = db.query(models.ProductReview).filter(
        models.ProductReview.product_id == product_id,
        models.ProductReview.user_id == current_user.id,
    ).first()
    if already:
        return {"can_review": False, "reason": "already_reviewed"}

    if not _user_bought_product(db, current_user.id, product_id):
        return {"can_review": False, "reason": "not_purchased"}

    return {"can_review": True, "reason": None}


@router.get("/mine")
def get_my_reviews(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_login),
):
    """Return list of product_ids the current user has already reviewed."""
    reviews = db.query(models.ProductReview).filter(
        models.ProductReview.user_id == current_user.id
    ).all()
    return [{"product_id": r.product_id, "stars": r.stars} for r in reviews]


@router.post("", status_code=201)
def submit_review(
    body: ReviewIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_login),
):
    product = db.query(models.Product).filter(models.Product.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    already = db.query(models.ProductReview).filter(
        models.ProductReview.product_id == body.product_id,
        models.ProductReview.user_id == current_user.id,
    ).first()
    if already:
        raise HTTPException(status_code=400, detail="Bạn đã đánh giá sản phẩm này rồi")

    if not _user_bought_product(db, current_user.id, body.product_id):
        raise HTTPException(status_code=403, detail="Chỉ khách hàng đã mua sản phẩm mới có thể đánh giá")

    review = models.ProductReview(
        product_id=body.product_id,
        user_id=current_user.id,
        stars=body.stars,
        comment=body.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {"success": True, "message": "Cảm ơn bạn đã đánh giá!"}
