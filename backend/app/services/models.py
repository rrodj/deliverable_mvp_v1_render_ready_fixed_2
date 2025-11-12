from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Numeric, Date
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def _uuid():
    return str(uuid.uuid4())

class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(String, primary_key=True, default=_uuid)
    sku = Column(String, nullable=False, index=True, unique=True)
    name = Column(String, nullable=False)
    price = Column(Numeric(10,2), nullable=False, default=0)
    on_hand = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now())

class Calibration(Base):
    __tablename__ = "calibrations"
    id = Column(String, primary_key=True, default=_uuid)
    device_id = Column(String, nullable=False)
    offset = Column(Float, nullable=False, default=0.0)
    note = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=_uuid)
    type = Column(String, nullable=False)
    level = Column(String, nullable=False, default="info")
    message = Column(Text, nullable=False)
    sku = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class BillingEvent(Base):
    __tablename__ = "billing_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    ts = Column(Integer, nullable=False)
    payload = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

class BillingState(Base):
    __tablename__ = "billing_state"
    id = Column(Integer, primary_key=True, default=1)
    state = Column(JSON, nullable=False, default={})

class SalesRecord(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    sku = Column(String, nullable=False, index=True)
    qty = Column(Integer, nullable=False, default=0)
    unit_price = Column(Numeric(10,2), nullable=False, default=0)
    discount_rate = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, server_default=func.now())

class RoiSnapshot(Base):
    __tablename__ = "roi_snapshots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(String, nullable=False)
    total_protected_usd = Column(Numeric(12,2), nullable=False, default=0)
    components = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, server_default=func.now())

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(String, nullable=False)
    category = Column(String, nullable=False)   # dead_stock | stockout_risk | promo_bleed
    status = Column(String, nullable=False, default="potential")  # potential | protected
    sku = Column(String)
    item_name = Column(String)
    amount_usd = Column(Numeric(12,2), nullable=False, default=0)
    inputs = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
