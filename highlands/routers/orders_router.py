"""
Orders endpoints:
  POST /api/orders               — create order (guest or logged-in)
  GET  /api/orders/mine          — order history for current user (auth required)
  GET  /api/orders               — all orders (admin only)
  PATCH /api/orders/{id}/cancel  — cancel pending order
"""
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from highlands.database import get_db
from highlands import models
from highlands.auth_utils import get_current_user, require_admin, require_login

router = APIRouter(prefix="/api/orders", tags=["orders"])


# ── Schemas ───────────────────────────────────────────────

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1, le=100)

class OrderIn(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    address: Optional[str] = Field(default="", max_length=300)
    items: list[OrderItemIn] = Field(..., min_length=1, max_length=50)
    note: Optional[str] = Field(default="", max_length=500)
    payment_method: Optional[str] = "cash"  # cash | qr_transfer

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
    pay_method = body.payment_method if body.payment_method in ("cash", "qr_transfer") else "cash"

    total = 0
    item_rows = []
    for item in body.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product or not product.is_active:
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
        payment_method=pay_method,
        payment_status="unpaid",
    )
    db.add(order)
    db.flush()

    for row in item_rows:
        row.order_id = order.id
        db.add(row)

    # Cộng điểm cho user đã đăng nhập: 10.000đ = 1 điểm
    earned_points = total // 10000
    if earned_points > 0 and current_user:
        current_user.points = (current_user.points or 0) + earned_points

    db.commit()
    db.refresh(order)

    return {
        "message": "Đặt hàng thành công!",
        "earned_points": earned_points,
        "order": {
            "id": order.id,
            "customer_name": order.customer_name,
            "total": order.total,
            "status": order.status,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
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
            "payment_method": o.payment_method or "cash",
            "payment_status": o.payment_status or "unpaid",
            "note": o.note,
            "created_at": o.created_at.strftime("%d/%m/%Y %H:%M"),
            "items": [{"product_id": i.product_id, "name": i.name, "price": i.price, "quantity": i.quantity, "subtotal": i.subtotal} for i in o.items],
        }
        for o in orders
    ]


@router.get("")
def all_orders(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin only: list all orders."""
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
    cancel_token: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    """Cancel a pending order.
    - Logged-in users: must own the order.
    - Guest orders: must supply the cancel_token returned at order creation.
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    if order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Không thể hủy đơn hàng ở trạng thái '{order.status}'",
        )

    if order.user_id is not None:
        # Logged-in order: must be the owner
        if current_user is None or current_user.id != order.user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền hủy đơn hàng này")
    else:
        # Guest order: require valid cancel_token
        if not cancel_token or not order.cancel_token or cancel_token != order.cancel_token:
            raise HTTPException(status_code=403, detail="Token hủy đơn không hợp lệ")

    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return {"message": "Đơn hàng đã được hủy thành công", "order_id": order.id, "status": order.status}
