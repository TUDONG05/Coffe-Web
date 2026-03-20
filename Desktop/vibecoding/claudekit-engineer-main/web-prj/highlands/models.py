"""
SQLAlchemy ORM models: User, Product, Order, OrderItem.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from highlands.database import Base


class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, index=True, nullable=False)
    phone      = Column(String(20), nullable=True)
    hashed_pwd = Column(String(255), nullable=False)
    role       = Column(String(20), default="customer", nullable=False)  # admin, staff, customer
    is_active  = Column(Integer, default=1)  # for block/unblock
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user")


class Category(Base):
    __tablename__ = "categories"
    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String(100), unique=True, nullable=False)
    emoji    = Column(String(10), default="☕")
    is_active = Column(Integer, default=1)


class Product(Base):
    __tablename__ = "products"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(150), nullable=False)
    category    = Column(String(50), nullable=False)   # coffee/tea/food/smoothie
    price       = Column(Integer, nullable=False)       # VND
    description = Column(Text, nullable=True)
    emoji       = Column(String(10), default="☕")
    is_active   = Column(Integer, default=1)


class Order(Base):
    __tablename__ = "orders"
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_name = Column(String(100), nullable=False)
    phone         = Column(String(20), nullable=False)
    total         = Column(Integer, nullable=False)
    note          = Column(Text, nullable=True)
    status        = Column(String(30), default="pending")  # pending/confirmed/done
    is_active     = Column(Integer, default=1)  # soft delete
    created_at    = Column(DateTime, default=datetime.utcnow)

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


class Promotion(Base):
    __tablename__ = "promotions"
    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    discount    = Column(String(50), nullable=True)   # e.g. "20%", "Mua 1 tặng 1"
    emoji       = Column(String(10), default="🎁")
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
    emoji        = Column(String(10), default="📰")
    published_at = Column(String(50), nullable=True)
    is_active    = Column(Integer, default=1)
