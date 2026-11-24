from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, JSON # <-- добавили JSON

from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, default="retail", nullable=False)
    wholesale_status = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    unp = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    legal_address = Column(String, nullable=True)

    orders = relationship("Order", back_populates="user")




class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    group_id = Column(String, index=True, nullable=True)
    color_name = Column(String, nullable=True)
    category = Column(String, index=True, nullable=False)
    subcategory = Column(String, index=True, nullable=True)
    name = Column(String, nullable=False)
    specs = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    mechanism = Column(String, nullable=True)
    case_material = Column(String, nullable=True)
    warranty = Column(String, default="12 месяцев")
    
    # <-- НОВОЕ: Гибкий список характеристик для админки: [{"label": "Механизм", "value": "Кварцевый"}]
    attributes = Column(JSON, nullable=True)
    
    icon = Column(String, default="⌚")
    image = Column(String, nullable=True)

    retail_price = Column(Float, nullable=False)
    wholesale_price = Column(Float, nullable=False)
    min_wholesale_qty = Column(Integer, default=5)
    stock = Column(Integer, default=20, nullable=False)

    # <-- НОВОЕ: Скидки и акции
    old_retail_price = Column(Float, nullable=True)
    old_wholesale_price = Column(Float, nullable=True)
    promo_label = Column(String, nullable=True)






class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True, nullable=False)  # Например: СТ-0001
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    role = Column(String, default="retail")
    status = Column(String, default="processing")  # processing, europost_pending, shipped, ready_pickup, completed
    track_code = Column(String, nullable=True)

    recipient_name = Column(String, nullable=False)
    recipient_phone = Column(String, nullable=False)

    delivery_method = Column(String, nullable=False)  # 'europost' или 'pickup'
    delivery_city = Column(String, nullable=True)
    delivery_office = Column(String, nullable=True)

    company_name = Column(String, nullable=True)
    unp = Column(String(9), nullable=True)

    comment = Column(Text, nullable=True)
    products_total_byn = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer)
    sku = Column(String)
    name = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Float)

    order = relationship("Order", back_populates="items")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    icon = Column(String, default="⌚", nullable=False)
    subcategories = Column(JSON, default=list, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
