"""Admin user/account management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import require_admin, hash_password

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    role: str
    is_active: int
    created_at: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    password: str
    role: str  # "admin" or "staff"


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    role: str | None = None


class UserStatusUpdate(BaseModel):
    is_active: int


class PaginatedUsers(BaseModel):
    items: list[UserOut]
    total: int
    skip: int
    limit: int
    has_next: bool


@router.get("", response_model=PaginatedUsers)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[int] = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List admin and staff accounts."""
    query = db.query(models.User).filter(
        models.User.role.in_(["admin", "staff"])
    )

    if role:
        query = query.filter(models.User.role == role)

    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)

    if search:
        query = query.filter(
            models.User.name.ilike(f"%{search}%")
            | models.User.email.ilike(f"%{search}%")
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
            "role": item.role,
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


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get a single user account."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.post("", status_code=201, response_model=UserOut)
def create_user(
    body: UserCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new admin or staff account."""
    if body.role not in ["admin", "staff"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'staff'")

    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = models.User(
        name=body.name,
        email=body.email,
        phone=body.phone,
        hashed_pwd=hash_password(body.password),
        role=body.role,
        is_active=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update user information."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.email:
        existing = db.query(models.User).filter(
            models.User.email == body.email,
            models.User.id != user_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = body.email

    if body.name:
        user.name = body.name
    if body.phone:
        user.phone = body.phone
    if body.role:
        if body.role not in ["admin", "staff"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = body.role

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.patch("/{user_id}", response_model=UserOut)
def update_user_status(
    user_id: int,
    body: UserStatusUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Toggle user account status (active/inactive)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deactivating the last admin
    if body.is_active == 0 and user.role == "admin":
        admin_count = db.query(models.User).filter(
            models.User.role == "admin",
            models.User.is_active == 1,
        ).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot deactivate the last admin")

    user.is_active = body.is_active
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Soft delete a user account (set is_active=0)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deleting the last admin
    if user.role == "admin":
        admin_count = db.query(models.User).filter(
            models.User.role == "admin",
            models.User.is_active == 1,
        ).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin")

    user.is_active = 0
    db.commit()

    return {"success": True, "message": "User deleted successfully"}
