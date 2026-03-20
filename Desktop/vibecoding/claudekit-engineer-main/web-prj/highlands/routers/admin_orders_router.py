"""Admin order management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import require_admin

router = APIRouter(prefix="/api/admin/orders", tags=["admin-orders"])


class OrderItemOut(BaseModel):
    id: int
    product_id: int | None
    name: str
    price: int
    quantity: int
    subtotal: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    customer_name: str
    phone: str
    total: int
    note: str | None
    status: str
    created_at: str
    user_id: int | None
    items: list[OrderItemOut]

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    note: str | None = None
    items: list[OrderItemCreate]


class PaginatedOrders(BaseModel):
    items: list[OrderOut]
    total: int
    skip: int
    limit: int
    has_next: bool


@router.get("", response_model=PaginatedOrders)
def list_orders(
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    search: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    min_total: int | None = None,
    max_total: int | None = None,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(models.Order).filter(models.Order.is_active == 1)

    if status:
        query = query.filter(models.Order.status == status)

    if search:
        query = query.filter(
            models.Order.customer_name.ilike(f"%{search}%")
            | models.Order.phone.ilike(f"%{search}%")
        )

    if start_date:
        from datetime import datetime
        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(models.Order.created_at >= start)
        except:
            pass

    if end_date:
        from datetime import datetime
        try:
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(models.Order.created_at <= end)
        except:
            pass

    if min_total is not None:
        query = query.filter(models.Order.total >= min_total)

    if max_total is not None:
        query = query.filter(models.Order.total <= max_total)

    total = query.count()
    db_items = query.order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()

    items = []
    for order in db_items:
        items.append({
            "id": order.id,
            "customer_name": order.customer_name,
            "phone": order.phone,
            "total": order.total,
            "note": order.note,
            "status": order.status,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None,
            "user_id": order.user_id,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "name": item.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "subtotal": item.subtotal,
                }
                for item in (order.items or [])
            ],
        })

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_next": skip + limit < total,
    }


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "phone": order.phone,
        "total": order.total,
        "note": order.note,
        "status": order.status,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None,
        "user_id": order.user_id,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "name": item.name,
                "price": item.price,
                "quantity": item.quantity,
                "subtotal": item.subtotal,
            }
            for item in (order.items or [])
        ],
    }


@router.patch("/{order_id}", response_model=OrderOut)
def update_order_status(
    order_id: int,
    body: OrderStatusUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Not found")

    valid_statuses = ["pending", "confirmed", "done"]
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    order.status = body.status
    db.commit()
    db.refresh(order)

    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "phone": order.phone,
        "total": order.total,
        "note": order.note,
        "status": order.status,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None,
        "user_id": order.user_id,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "name": item.name,
                "price": item.price,
                "quantity": item.quantity,
                "subtotal": item.subtotal,
            }
            for item in (order.items or [])
        ],
    }


@router.post("", status_code=201, response_model=OrderOut)
def create_order(
    body: OrderCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new order with items."""
    if not body.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    total = 0
    order_items = []

    for item in body.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        subtotal = product.price * item.quantity
        total += subtotal

        order_items.append({
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": item.quantity,
            "subtotal": subtotal,
        })

    order = models.Order(
        customer_name=body.customer_name,
        phone=body.phone,
        total=total,
        note=body.note,
        status="pending",
        is_active=1,
    )
    db.add(order)
    db.flush()

    for item_data in order_items:
        order_item = models.OrderItem(
            order_id=order.id,
            **item_data,
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "phone": order.phone,
        "total": order.total,
        "note": order.note,
        "status": order.status,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None,
        "user_id": order.user_id,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "name": item.name,
                "price": item.price,
                "quantity": item.quantity,
                "subtotal": item.subtotal,
            }
            for item in (order.items or [])
        ],
    }


@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Soft delete an order (set is_active=0)."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.is_active = 0
    db.commit()

    return {"success": True, "message": "Order deleted successfully"}
