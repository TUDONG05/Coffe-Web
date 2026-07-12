"""
Admin endpoints for store management: CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import require_admin

router = APIRouter(prefix="/api/admin/stores", tags=["admin-stores"])


class StoreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=300)
    district: str = Field(..., min_length=1, max_length=100)
    city: str = "Hà Nội"
    phone: Optional[str] = None
    hours: str = "06:00 – 23:00"


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    hours: Optional[str] = None
    is_active: Optional[int] = None


class StoreOut(BaseModel):
    id: int
    name: str
    address: str
    district: str
    city: str
    phone: Optional[str]
    hours: str
    is_active: int

    class Config:
        from_attributes = True


class PaginatedStores(BaseModel):
    items: list[StoreOut]
    total: int
    skip: int
    limit: int
    has_next: bool


@router.get("", response_model=PaginatedStores)
def list_stores(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    city: Optional[str] = None,
    is_active: Optional[int] = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(models.Store)

    if search:
        query = query.filter(
            models.Store.name.ilike(f"%{search}%") |
            models.Store.address.ilike(f"%{search}%") |
            models.Store.district.ilike(f"%{search}%")
        )
    if city:
        query = query.filter(models.Store.city == city)
    if is_active is not None:
        query = query.filter(models.Store.is_active == is_active)

    total = query.count()
    items = query.order_by(models.Store.id).offset(skip).limit(limit).all()

    return {"items": items, "total": total, "skip": skip, "limit": limit, "has_next": skip + limit < total}


@router.post("", response_model=StoreOut, status_code=201)
def create_store(
    body: StoreCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    store = models.Store(
        name=body.name,
        address=body.address,
        district=body.district,
        city=body.city,
        phone=body.phone,
        hours=body.hours,
        is_active=1,
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
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Cửa hàng không tồn tại")

    for field in ("name", "address", "district", "city", "phone", "hours", "is_active"):
        val = getattr(body, field)
        if val is not None:
            setattr(store, field, val)

    db.commit()
    db.refresh(store)
    return store


@router.patch("/{store_id}", response_model=StoreOut)
def toggle_store(
    store_id: int,
    body: StoreUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Cửa hàng không tồn tại")

    if body.is_active is not None:
        store.is_active = body.is_active

    db.commit()
    db.refresh(store)
    return store


@router.delete("/{store_id}")
def delete_store(
    store_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Cửa hàng không tồn tại")

    db.delete(store)
    db.commit()
    return {"detail": "Đã xóa cửa hàng"}
