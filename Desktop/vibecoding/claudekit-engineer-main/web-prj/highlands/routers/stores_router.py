"""
Stores endpoints:
  GET /api/stores       — list all stores (optional ?city= filter, ?q= search)
  GET /api/stores/{id}  — store detail
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from highlands.database import get_db
from highlands import models

router = APIRouter(prefix="/api/stores", tags=["stores"])


class StoreOut(BaseModel):
    id: int
    name: str
    address: str
    district: str
    city: str
    phone: Optional[str]
    hours: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[StoreOut])
def list_stores(
    city: Optional[str] = Query(None, description="Filter by city name"),
    q: Optional[str] = Query(None, description="Search by name or address"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Store).filter(models.Store.is_active == 1)
    if city:
        query = query.filter(models.Store.city == city)
    if q:
        like = f"%{q}%"
        query = query.filter(
            models.Store.name.ilike(like) | models.Store.address.ilike(like)
        )
    return query.order_by(models.Store.city, models.Store.id).all()


@router.get("/cities", response_model=list[str])
def get_cities(db: Session = Depends(get_db)):
    """Get list of unique cities from stores"""
    cities = db.query(models.Store.city).filter(
        models.Store.is_active == 1
    ).distinct().order_by(models.Store.city).all()
    return [city[0] for city in cities if city[0]]


@router.get("/{store_id}", response_model=StoreOut)
def get_store(store_id: int, db: Session = Depends(get_db)):
    store = db.query(models.Store).filter(
        models.Store.id == store_id,
        models.Store.is_active == 1,
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail="Không tìm thấy cửa hàng")
    return store
