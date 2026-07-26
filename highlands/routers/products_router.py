"""
Products endpoints: GET /api/products, GET /api/products/{id},
POST /api/products/search-by-image, GET /api/products/{id}/similar
"""
import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel
from typing import Optional
from highlands.database import get_db
from highlands import models
from highlands.rate_limit import enforce_rate_limit
from highlands.services import image_search_service as img_svc
from highlands.services.image_search_service import image_search

logger = logging.getLogger(__name__)

# Ảnh truy vấn đã được resize 512px phía client (~80KB). 2MB là biên an toàn,
# nằm dưới hẳn giới hạn body ~4.5MB của Vercel serverless.
MAX_QUERY_IMAGE_BYTES = 2 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

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


def _rebuild_index(db: Session) -> None:
    """Nạp lại index ảnh từ DB. Cần cho serverless: cold start có thể xảy ra
    trước khi startup hook chạy xong, hoặc DB chưa sẵn sàng lúc đó."""
    products = db.query(models.Product).filter(models.Product.is_active == 1).all()
    image_search.build_index(products)


def _hits_to_products(hits: list[tuple[int, float]], db: Session) -> list[dict]:
    """Chuyển [(product_id, score)] thành list sản phẩm kèm score.

    Giữ nguyên thứ tự do search() trả về — truy vấn `WHERE id IN (...)`
    KHÔNG bảo toàn thứ tự nên phải sắp lại ở phía Python.
    """
    if not hits:
        return []

    scores = dict(hits)
    rows = db.query(models.Product).filter(
        models.Product.id.in_(list(scores)),
        models.Product.is_active == 1,
    ).all()
    by_id = {p.id: p for p in rows}

    ordered = [by_id[pid] for pid, _ in hits if pid in by_id]
    enriched = _with_ratings(ordered, db)
    for d in enriched:
        d["score"] = round(scores[d["id"]], 4)
    return enriched


@router.post("/search-by-image")
async def search_by_image(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Tìm sản phẩm giống nhất với ảnh người dùng gửi lên.

    Ảnh chỉ đi qua RAM để sinh embedding, không lưu lại ở đâu cả.
    """
    enforce_rate_limit(request, key="img-search", max_hits=10)

    if not img_svc.is_configured():
        raise HTTPException(status_code=503, detail="Tính năng tìm bằng ảnh chưa được cấu hình")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận JPEG, PNG, WebP")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File ảnh rỗng")
    if len(content) > MAX_QUERY_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Ảnh không được vượt quá 2MB")

    if not image_search.is_ready():
        _rebuild_index(db)
    if not image_search.is_ready():
        raise HTTPException(status_code=503, detail="Chưa có dữ liệu ảnh sản phẩm để so khớp")

    try:
        vec = await img_svc.embed_image_bytes(content)
    except Exception as e:
        logger.warning("Sinh embedding ảnh truy vấn thất bại: %s", e)
        raise HTTPException(
            status_code=502,
            detail="Không kết nối được dịch vụ nhận diện ảnh, vui lòng thử lại",
        )

    return _hits_to_products(image_search.search(vec, top_k=5), db)


@router.get("/{product_id}/similar")
def similar_products(product_id: int, limit: int = 4, db: Session = Depends(get_db)):
    """Món nhìn giống nhất với sản phẩm này. Không gọi API ngoài — chỉ tra
    ma trận embedding có sẵn, nên miễn phí và nhanh.

    Sản phẩm chưa có embedding trả về [] (200) để frontend tự ẩn khối.
    """
    if not image_search.is_ready():
        _rebuild_index(db)
    limit = max(1, min(limit, 12))
    return _hits_to_products(image_search.search_similar(product_id, top_k=limit), db)


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return _with_ratings([p], db)[0]
