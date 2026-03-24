"""Admin customer management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import require_admin, hash_password

router = APIRouter(prefix="/api/admin/customers", tags=["admin-customers"])


class CustomerStatusUpdate(BaseModel):
    is_active: int


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None
    password: str


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None


class CustomerOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    address: str | None
    role: str
    points: int
    is_active: int
    created_at: str

    class Config:
        from_attributes = True


class PaginatedCustomers(BaseModel):
    items: list[CustomerOut]
    total: int
    skip: int
    limit: int
    has_next: bool


@router.get("", response_model=PaginatedCustomers)
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(models.User)

    if role:
        query = query.filter(models.User.role == role)

    if status == "active":
        query = query.filter(models.User.is_active == 1)
    elif status == "blocked":
        query = query.filter(models.User.is_active == 0)

    if search:
        query = query.filter(
            models.User.name.ilike(f"%{search}%")
            | models.User.email.ilike(f"%{search}%")
            | models.User.phone.ilike(f"%{search}%")
        )

    total = query.count()
    db_items = query.order_by(models.User.created_at.desc()).offset(skip).limit(limit).all()

    items = []
    for item in db_items:
        items.append({
            "id": item.id,
            "name": item.name,
            "email": item.email,
            "phone": item.phone,
            "address": item.address,
            "role": item.role,
            "points": item.points or 0,
            "is_active": item.is_active,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_next": skip + limit < total,
    }


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    customer = db.query(models.User).filter(models.User.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "role": customer.role,
        "points": customer.points or 0,
        "is_active": customer.is_active,
        "created_at": customer.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer_status(
    customer_id: int,
    body: CustomerStatusUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    customer = db.query(models.User).filter(models.User.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Not found")

    customer.is_active = body.is_active
    db.commit()
    db.refresh(customer)

    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "role": customer.role,
        "points": customer.points or 0,
        "is_active": customer.is_active,
        "created_at": customer.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    customer = db.query(models.User).filter(models.User.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(customer)
    db.commit()
    return {"success": True, "message": "Deleted"}


@router.post("", status_code=201, response_model=CustomerOut)
def create_customer(
    body: CustomerCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new customer account."""
    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    customer = models.User(
        name=body.name,
        email=body.email,
        phone=body.phone,
        address=body.address,
        hashed_pwd=hash_password(body.password),
        role="user",
        is_active=1,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "role": customer.role,
        "points": customer.points or 0,
        "is_active": customer.is_active,
        "created_at": customer.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update customer information."""
    customer = db.query(models.User).filter(models.User.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if body.email:
        existing = db.query(models.User).filter(
            models.User.email == body.email,
            models.User.id != customer_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        customer.email = body.email

    if body.name:
        customer.name = body.name
    if body.phone is not None:
        customer.phone = body.phone
    if body.address is not None:
        customer.address = body.address

    db.commit()
    db.refresh(customer)

    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "role": customer.role,
        "points": customer.points or 0,
        "is_active": customer.is_active,
        "created_at": customer.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
