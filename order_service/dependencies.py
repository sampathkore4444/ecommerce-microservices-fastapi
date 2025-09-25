from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from .models import Order


def get_order_or_404(order_id: str, db: Session = Depends(get_db)):
    """REST API: Delete order (synchronous + asynchronous event)"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return order
