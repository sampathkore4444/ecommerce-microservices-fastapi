from sqlalchemy import Column, String, DateTime, Float, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
import datetime
from enum import Enum as PyEnum

Base = declarative_base()


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    items = Column(JSON)  # Store order items as JSON
    total_amount = Column(Float)
    status = Column(String, default=OrderStatus.PENDING)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def __repr__(self):
        return f"<Order(id='{self.id}', status='{self.status}', total={self.total_amount})>"
