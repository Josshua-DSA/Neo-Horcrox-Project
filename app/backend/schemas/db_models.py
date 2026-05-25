"""
app/backend/schemas/db_models.py
---------------------
SQLAlchemy ORM models untuk PostgreSQL.
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, DateTime, Text, JSON,
    Index, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


# ─── Table: orders ────────────────────────────────────────────────────────────

class Order(Base):
    """
    Satu baris di tabel `orders`.
    Mewakili satu baris dari DataCoSupplyChainDataset.
    """
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(Integer, unique=True, nullable=False, index=True)
    order_date = Column(DateTime, nullable=True, index=True)
    shipping_date = Column(DateTime, nullable=True)

    # Customer
    customer_id = Column(Integer, nullable=False, index=True)
    customer_segment = Column(String(50), nullable=True)
    customer_city = Column(String(100), nullable=True)
    customer_state = Column(String(100), nullable=True)
    customer_country = Column(String(100), nullable=True)

    # Shipping
    shipping_mode = Column(String(50), nullable=True)
    days_for_shipping_real = Column(Integer, nullable=True)
    days_for_shipment_scheduled = Column(Integer, nullable=True)
    delivery_status = Column(String(50), nullable=True)
    late_delivery_risk = Column(Integer, nullable=True, index=True)  # 0 or 1

    # Geography
    market = Column(String(50), nullable=True)
    order_region = Column(String(100), nullable=True)
    order_country = Column(String(100), nullable=True)
    order_city = Column(String(100), nullable=True)
    order_state = Column(String(100), nullable=True)

    # Financials
    sales_per_customer = Column(Float, nullable=True)
    benefit_per_order = Column(Float, nullable=True)
    order_profit_per_order = Column(Float, nullable=True)
    order_status = Column(String(50), nullable=True)
    type = Column(String(50), nullable=True)  # transaction type

    # Product
    product_card_id = Column(Integer, nullable=True)
    product_name = Column(String(255), nullable=True)
    product_price = Column(Float, nullable=True)
    product_status = Column(Integer, nullable=True)
    category_id = Column(Integer, nullable=True)
    category_name = Column(String(100), nullable=True)
    department_id = Column(Integer, nullable=True)
    department_name = Column(String(100), nullable=True)

    # Store geo
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Engineered features (opsional)
    actual_delay = Column(Float, nullable=True)
    shipping_speed_ratio = Column(Float, nullable=True)
    has_price_inconsistency = Column(Integer, nullable=True)
    country_mismatch = Column(Integer, nullable=True)
    state_mismatch = Column(Integer, nullable=True)
    city_mismatch = Column(Integer, nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != "id"}


# ─── Table: order_items ───────────────────────────────────────────────────────

class OrderItem(Base):
    """
    Satu baris di tabel `order_items`.
    Relasi ke orders via order_id.
    """
    __tablename__ = "order_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_item_id = Column(Integer, unique=True, nullable=False, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    product_card_id = Column(Integer, nullable=True)
    order_item_cardprod_id = Column(Integer, nullable=True)
    order_item_quantity = Column(Integer, nullable=True)
    order_item_product_price = Column(Float, nullable=True)
    order_item_discount = Column(Float, nullable=True)
    order_item_discount_rate = Column(Float, nullable=True)
    order_item_profit_ratio = Column(Float, nullable=True)
    sales = Column(Float, nullable=True)
    order_item_total = Column(Float, nullable=True)

    # Engineered
    calculated_item_total = Column(Float, nullable=True)
    item_total_gap = Column(Float, nullable=True)
    abs_item_total_gap = Column(Float, nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != "id"}


# ─── Table: predictions ──────────────────────────────────────────────────────

class PredictionLog(Base):
    """
    Log setiap kali endpoint /risk/predict dipanggil.
    Berguna untuk monitoring model drift.
    """
    __tablename__ = "predictions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=True, index=True)
    prediction = Column(Integer, nullable=False, index=True)
    probability_late = Column(Float, nullable=False)
    probability_on_time = Column(Float, nullable=False)
    label = Column(String(50), nullable=False)
    model_version = Column(String(20), nullable=False)
    input_snapshot = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != "id"}


# ─── Table: forecast_logs ────────────────────────────────────────────────────

class ForecastLog(Base):
    __tablename__ = "forecast_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_name = Column(String(100), nullable=False, index=True)
    market = Column(String(50), nullable=False)
    periods = Column(Integer, nullable=False)
    forecast_result = Column(JSON, nullable=False)
    model_version = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != "id"}
