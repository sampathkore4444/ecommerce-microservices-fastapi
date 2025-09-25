import pytest
from fastapi import HTTPException
from order_service.dependencies import get_order_or_404
from order_service.models import Order, OrderStatus


class TestOrderDependencies:
    def test_get_order_or_404_found(self, db_session, test_order):
        """Test dependency returns order when exists"""
        order = get_order_or_404(test_order.id, db_session)

        assert order is not None
        assert order.id == test_order.id
        assert order.user_id == test_order.user_id
        assert order.total_amount == test_order.total_amount

    def test_get_order_or_404_not_found(self, db_session):
        """Test dependency raises 404 when order not found"""
        with pytest.raises(HTTPException) as exc_info:
            get_order_or_404("non-existent-id", db_session)

        assert exc_info.value.status_code == 404
        assert "Order not found" in exc_info.value.detail

    def test_get_order_or_404_invalid_id(self, db_session):
        """Test dependency with various invalid IDs"""
        invalid_ids = ["", None, "invalid-order-id"]

        for invalid_id in invalid_ids:
            with pytest.raises(HTTPException) as exc_info:
                get_order_or_404(invalid_id, db_session)

            assert exc_info.value.status_code == 404

    def test_get_order_or_404_deleted_order(self, db_session, test_order):
        """Test dependency doesn't find deleted orders"""
        # Delete the order
        db_session.delete(test_order)
        db_session.commit()

        # Try to get deleted order
        with pytest.raises(HTTPException) as exc_info:
            get_order_or_404(test_order.id, db_session)

        assert exc_info.value.status_code == 404
