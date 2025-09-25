from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from ..database import get_db
from ..models import Order, OrderStatus
from shared.schemas import OrderCreate, OrderResponse, OrderItem

from dependencies import get_order_or_404

from ..event_handlers import (
    publish_order_created,
    publish_order_updated,
    publish_order_cancelled,
)


router = APIRouter(prefix="/orders", tags=["orders"])


# 🔄 REST API ENDPOINTS (Synchronous)
@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    order_id = str(uuid.uuid4())

    # Convert Pydantic model to JSON-serializable dict
    items_json = [item.dict() for item in order.items]

    # Create order in database
    db_order = Order(
        id=order_id,
        user_id="current-user-id",  # In real app, get from auth
        items=items_json,
        total_amount=order.total_amount,
        status=OrderStatus.PENDING,
    )

    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # 🎯 MESSAGE QUEUE: Publish event asynchronously
    order_response = OrderResponse(
        id=db_order.id,
        user_id=db_order.user_id,
        items=[OrderItem(**item) for item in db_order.items],
        total_amount=db_order.total_amount,
        status=db_order.status,
        created_at=db_order.created_at,
    )

    await publish_order_created(order_response)

    # return db_order
    return order_response


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """REST API: Get orders (synchronous)"""
    query = db.query(Order)

    if user_id:
        query = query.filter(Order.user_id == user_id)

    if status:
        query = query.filter(Order.status == status)

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    # return orders

    # Convert to response model
    return [
        OrderResponse(
            id=order.id,
            user_id=order.user_id,
            items=[OrderItem(**item) for item in order.items],
            total_amount=order.total_amount,
            status=order.status,
            created_at=order.created_at,
        )
        for order in orders
    ]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order: Order = Depends(get_order_or_404)):

    # return order
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        items=[OrderItem(**item) for item in order.items],
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
    )


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    status_update: dict,
    order: Order = Depends(get_order_or_404),
    db: Session = Depends(get_db),
):
    new_status = status_update.get("status")

    if new_status not in [status.value for status in OrderStatus]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {[status.value for status in OrderStatus]}",
        )

    # Update order
    order.status = new_status
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)

    # 🎯 MESSAGE QUEUE: Publish update event
    order_response = OrderResponse(
        id=order.id,
        user_id=order.user_id,
        items=[OrderItem(**item) for item in order.items],
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
    )

    await publish_order_updated(order_response)

    # return order
    return order_response


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order: Order = Depends(get_order_or_404), db: Session = Depends(get_db)
):

    # 🎯 MESSAGE QUEUE: Publish cancellation event before deletion
    order_response = OrderResponse(
        id=order.id,
        user_id=order.user_id,
        items=[OrderItem(**item) for item in order.items],
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
    )

    await publish_order_cancelled(order_response)

    # Delete from database
    db.delete(order)
    db.commit()


@router.get("/user/{user_id}/orders", response_model=List[OrderResponse])
async def get_user_orders(user_id: str, db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders
