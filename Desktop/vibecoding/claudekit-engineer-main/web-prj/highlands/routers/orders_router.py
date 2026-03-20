"""
Orders endpoints:
  POST /api/orders        — create order (guest or logged-in)
  GET  /api/orders/mine   — order history for current user (auth required)
  GET  /api/orders        — all orders (admin, no auth for demo)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])


# ── Schemas ───────────────────────────────────────────────

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int

class OrderIn(BaseModel):
    customer_name: str
    phone: str
    address: Optional[str] = ""
    items: list[OrderItemIn]
    note: Optional[str] = ""

class OrderItemOut(BaseModel):
    product_id: int
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
    note: Optional[str]
    status: str
    created_at: str
    items: list[OrderItemOut]

    class Config:
        from_attributes = True


# ── Routes ────────────────────────────────────────────────

@router.post("", status_code=201)
def create_order(
    body: OrderIn,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    total = 0
    item_rows = []
    for item in body.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Sản phẩm #{item.product_id} không tồn tại")
        subtotal = product.price * item.quantity
        total += subtotal
        item_rows.append(models.OrderItem(
            product_id=product.id,
            name=product.name,
            price=product.price,
            quantity=item.quantity,
            subtotal=subtotal,
        ))

    order = models.Order(
        user_id=current_user.id if current_user else None,
        customer_name=body.customer_name,
        phone=body.phone,
        address=body.address,
        total=total,
        note=body.note,
    )
    db.add(order)
    db.flush()  # get order.id before committing

    for row in item_rows:
        row.order_id = order.id
        db.add(row)

    db.commit()
    db.refresh(order)
    return {
        "message": "Đặt hàng thành công!",
        "order": {
            "id": order.id,
            "customer_name": order.customer_name,
            "total": order.total,
            "status": order.status,
            "items": [{"name": r.name, "price": r.price, "quantity": r.quantity, "subtotal": r.subtotal} for r in order.items],
        }
    }


@router.get("/mine")
def my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return orders for the currently logged-in user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Vui lòng đăng nhập")
    orders = (
        db.query(models.Order)
        .filter(models.Order.user_id == current_user.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )
    return [
        {
            "id": o.id,
            "customer_name": o.customer_name,
            "total": o.total,
            "status": o.status,
            "note": o.note,
            "created_at": o.created_at.strftime("%d/%m/%Y %H:%M"),
            "items": [{"name": i.name, "price": i.price, "quantity": i.quantity, "subtotal": i.subtotal} for i in o.items],
        }
        for o in orders
    ]


@router.get("")
def all_orders(db: Session = Depends(get_db)):
    """Admin: list all orders."""
    orders = db.query(models.Order).order_by(models.Order.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "customer_name": o.customer_name,
            "phone": o.phone,
            "total": o.total,
            "status": o.status,
            "created_at": o.created_at.strftime("%d/%m/%Y %H:%M"),
            "items_count": len(o.items),
        }
        for o in orders
    ]


@router.patch("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    """Cancel a pending order. Only the owner (logged-in) or a guest order may cancel."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    if order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Không thể hủy đơn hàng ở trạng thái '{order.status}'",
        )

    # Authorization: logged-in user must own the order; guest orders (user_id=None) are always cancellable
    if order.user_id is not None:
        if current_user is None or current_user.id != order.user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền hủy đơn hàng này")

    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return {"message": "Đơn hàng đã được hủy thành công", "order_id": order.id, "status": order.status}
