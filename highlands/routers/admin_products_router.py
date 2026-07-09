"""
Admin endpoints for product management: CRUD operations.
"""
import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import require_admin

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "images", "products")

router = APIRouter(prefix="/api/admin/products", tags=["admin-products"])


# ── Schemas ────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    category: str = Field(..., min_length=1, max_length=50)
    price: int = Field(..., gt=0)
    description: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    price: int | None = None
    description: str | None = None
    is_active: int | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    price: int
    description: str | None
    image_url: str | None
    is_active: int

    class Config:
        from_attributes = True


class PaginatedProducts(BaseModel):
    items: list[ProductOut]
    total: int
    skip: int
    limit: int
    has_next: bool


# ── Routes ─────────────────────────────────────────────────

@router.get("", response_model=PaginatedProducts)
def list_products(
    skip: int = 0,
    limit: int = 20,
    category: str | None = None,
    search: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    is_active: int | None = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all products with pagination and filters."""
    query = db.query(models.Product)

    if category:
        query = query.filter(models.Product.category == category)

    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))

    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)

    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)

    if is_active is not None:
        query = query.filter(models.Product.is_active == is_active)

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_next": skip + limit < total,
    }


@router.post("", response_model=ProductOut, status_code=201)
def create_product(
    body: ProductCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new product."""
    product = models.Product(
        name=body.name,
        category=body.category,
        price=body.price,
        description=body.description,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get product details."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    body: ProductUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update product details."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    if body.name is not None:
        product.name = body.name
    if body.category is not None:
        product.category = body.category
    if body.price is not None:
        product.price = body.price
    if body.description is not None:
        product.description = body.description

    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductOut)
def update_product_status(
    product_id: int,
    body: ProductUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update product status (is_active field only)."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    if hasattr(body, 'is_active') and body.is_active is not None:
        product.is_active = body.is_active

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Soft delete a product."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    product.is_active = 0
    db.commit()
    return {"success": True, "message": "Sản phẩm đã được xóa"}


@router.post("/{product_id}/image", response_model=ProductOut)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Upload product image. Accepts jpeg/png/webp, max 5MB."""
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận JPEG, PNG, WebP")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ảnh không được vượt quá 5MB")

    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    filename = f"{product_id}_{uuid.uuid4().hex[:8]}.{ext}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(UPLOAD_DIR, filename)

    # Remove old image file if exists
    if product.image_url:
        old_path = os.path.join(os.path.dirname(__file__), "..", "..", product.image_url.lstrip("/"))
        if os.path.exists(old_path):
            os.remove(old_path)

    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)

    product.image_url = f"/static/images/products/{filename}"
    db.commit()
    db.refresh(product)
    return product
