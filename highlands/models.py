"""
SQLAlchemy ORM models: User, Product, Order, OrderItem.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from highlands.database import Base

_VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def vn_now() -> datetime:
    """Return current time as naive datetime in Vietnam timezone (UTC+7)."""
    return datetime.now(_VN_TZ).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, index=True, nullable=False)
    phone      = Column(String(20), nullable=True)
    hashed_pwd = Column(String(255), nullable=True)   # nullable for Google-only users
    google_id  = Column(String(255), unique=True, nullable=True, index=True)
    role       = Column(String(20), default="user", nullable=False)  # admin, user
    address    = Column(String(300), nullable=True)
    points     = Column(Integer, default=0, nullable=False)
    is_active  = Column(Integer, default=1)  # for block/unblock
    created_at = Column(DateTime, default=vn_now)

    orders = relationship("Order", back_populates="user")


class Category(Base):
    __tablename__ = "categories"
    id        = Column(Integer, primary_key=True, index=True)
    name      = Column(String(100), unique=True, nullable=False)
    image_url = Column(String(300), nullable=True)
    is_active = Column(Integer, default=1)


class Product(Base):
    __tablename__ = "products"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(150), nullable=False)
    category    = Column(String(50), nullable=False)   # coffee/tea/food/smoothie
    price       = Column(Integer, nullable=False)       # VND
    description = Column(Text, nullable=True)
    image_url   = Column(String(300), nullable=True)
    video_url   = Column(String(500), nullable=True)
    is_active   = Column(Integer, default=1)
    # CLIP embedding của ảnh sản phẩm — JSON array 512 float đã chuẩn hoá L2
    image_embedding        = Column(Text, nullable=True)
    # image_url tại thời điểm sinh embedding; khác image_url hiện tại = embedding đã cũ
    image_embedding_source = Column(String(300), nullable=True)


class Order(Base):
    __tablename__ = "orders"
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_name = Column(String(100), nullable=False)
    phone         = Column(String(20), nullable=False)
    total         = Column(Integer, nullable=False)
    address       = Column(String(300), nullable=True)
    note          = Column(Text, nullable=True)
    status         = Column(String(30), default="pending")   # pending/confirmed/done
    payment_method = Column(String(20), default="cash")       # cash / qr_transfer
    payment_status = Column(String(20), default="unpaid")     # unpaid / paid
    cancel_token   = Column(String(32), nullable=True)        # guest order cancel token
    is_active      = Column(Integer, default=1)  # soft delete
    created_at    = Column(DateTime, default=vn_now)

    user  = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    id         = Column(Integer, primary_key=True, index=True)
    order_id   = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name       = Column(String(150), nullable=False)   # snapshot at order time
    price      = Column(Integer, nullable=False)
    quantity   = Column(Integer, nullable=False)
    subtotal   = Column(Integer, nullable=False)

    order   = relationship("Order", back_populates="items")
    product = relationship("Product")


class ProductReview(Base):
    __tablename__ = "product_reviews"
    id         = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    stars      = Column(Integer, nullable=False)   # 1-5
    comment    = Column(Text, nullable=True)
    created_at = Column(DateTime, default=vn_now)

    product = relationship("Product")
    user    = relationship("User")


class Promotion(Base):
    __tablename__ = "promotions"
    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    discount    = Column(String(50), nullable=True)   # e.g. "20%", "Mua 1 tặng 1"
    image_url   = Column(String(300), nullable=True)
    tag         = Column(String(50), nullable=True)   # "HOT", "NEW", "SALE"
    valid_until = Column(String(50), nullable=True)
    is_active   = Column(Integer, default=1)


class Store(Base):
    __tablename__ = "stores"
    id        = Column(Integer, primary_key=True, index=True)
    name      = Column(String(200), nullable=False)
    address   = Column(String(300), nullable=False)
    district  = Column(String(100), nullable=False)
    city      = Column(String(100), default="Hà Nội")
    phone     = Column(String(30), nullable=True)
    hours     = Column(String(100), default="06:00 – 23:00")
    is_active = Column(Integer, default=1)


class News(Base):
    __tablename__ = "news"
    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(300), nullable=False)
    excerpt      = Column(Text, nullable=True)
    content      = Column(Text, nullable=True)
    tag          = Column(String(50), nullable=True)   # "Tin Tức", "Sự Kiện", "Khuyến Mãi"
    image_url         = Column(String(300), nullable=True)
    video_url         = Column(String(500), nullable=True)
    published_at      = Column(String(50), nullable=True)
    view_count        = Column(Integer, default=0)
    unique_view_count = Column(Integer, default=0)
    is_active         = Column(Integer, default=1)
