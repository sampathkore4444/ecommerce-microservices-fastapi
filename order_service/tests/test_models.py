import pytest
from datetime import datetime
from order_service.models import Order, OrderStatus


class TestOrderModel:
    def test_order_creation(self, db_session):
        """Test order model creation with valid data"""
        order_items = [
            {"product_id": "prod-1", "quantity": 1, "price": 19.99},
            {"product_id": "prod-2", "quantity": 3, "price": 9.99},
        ]

        order = Order(
            user_id="user-123",
            items=order_items,
            total_amount=19.99 + (3 * 9.99),  # 49.96
            status=OrderStatus.PENDING,
        )
        db_session.add(order)
        db_session.commit()

        assert order.id is not None
        assert order.user_id == "user-123"
        assert len(order.items) == 2
        assert order.total_amount == 49.96
        assert order.status == OrderStatus.PENDING
        assert isinstance(order.created_at, datetime)

    def test_order_default_status(self, db_session):
        """Test order model uses default status"""
        order = Order(
            user_id="user-123",
            items=[{"product_id": "prod-1", "quantity": 1, "price": 10.0}],
            total_amount=10.0,
            # status should default to PENDING
        )
        db_session.add(order)
        db_session.commit()

        assert order.status == OrderStatus.PENDING

    def test_order_repr(self, db_session):
        """Test order string representation"""
        order = Order(
            user_id="user-123",
            items=[{"product_id": "prod-1", "quantity": 1, "price": 10.0}],
            total_amount=10.0,
            status=OrderStatus.CONFIRMED,
        )
        db_session.add(order)
        db_session.commit()

        assert "order-" in repr(order)  # Should contain order ID
        assert "confirmed" in repr(order).lower()
        assert "10.0" in repr(order)

    def test_order_status_enum(self):
        """Test order status enum values"""
        assert OrderStatus.PENDING == "pending"
        assert OrderStatus.CONFIRMED == "confirmed"
        assert OrderStatus.SHIPPED == "shipped"
        assert OrderStatus.DELIVERED == "delivered"
        assert OrderStatus.CANCELLED == "cancelled"
