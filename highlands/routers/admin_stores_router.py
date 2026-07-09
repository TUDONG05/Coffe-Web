"""
Admin endpoints for store management: CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import require_admin

router = APIRouter(prefix="/api/admin/stores", tags=["admin-stores"])


# ── Schemas ────────────────────────────────────────────────

class StoreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=300)
    district: str = Field(..., min_length=1, max_length=100)
    city: str = "Hà Nội"
    phone: str | None = None
    hours: str = "06:00 – 23:00"


class StoreUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    district: str | None = None
    city: str | None = None
    phone: str | None = None
    hours: str | None = None


class StoreOut(BaseModel):
    id: int
    name: str
    address: str
    district: str
    city: str
    phone: str | None
    hours: str
    is_active: int

    class Config:
        from_attributes = True


# ── Routes ─────────────────────────────────────────────────

@router.get("", response_model=list[StoreOut])
def list_stores(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all stores."""
    stores = db.query(models.Store).all()
    return stores


@router.post("", response_model=StoreOut, status_code=201)
def create_store(
    body: StoreCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new store."""
    store = models.Store(
        name=body.name,
        address=body.address,
        district=body.district,
        city=body.city,
        phone=body.phone,
        hours=body.hours,
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.get("/{store_id}", response_model=StoreOut)
def get_store(
    store_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get store details."""
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Cửa hàng không tồn tại")
    return store


@router.put("/{store_id}", response_model=StoreOut)
def update_store(
    store_id: int,
    body: StoreUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update store details."""
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Cửa hàng không tồn tại")

    if body.name is not None:
        store.name = body.name
    if body.address is not None:
        store.address = body.address
    if body.district is not None:
        store.district = body.district
    if body.city is not None:
        store.city = body.city
    if body.phone is not None:
        store.phone = body.phone
    if body.hours is not None:
        store.hours = body.hours

    db.commit()
    db.refresh(store)
    return store


@router.delete("/{store_id}")
def delete_store(
    store_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a store."""
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Cửa hàng không tồn tại")

    db.delete(store)
    db.commit()
    return {"success": True, "message": "Cửa hàng đã được xóa"}
