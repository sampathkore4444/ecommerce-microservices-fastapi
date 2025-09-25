import pytest


class TestOrderRoutes:
    def test_create_order_success(self, client, db_session):
        """Test successful order creation"""
        order_data = {
            "items": [{"product_id": "prod-123", "quantity": 2, "price": 29.99}],
            "total_amount": 59.98,
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["total_amount"] == 59.98
        assert len(data["items"]) == 1

    def test_get_orders_empty(self, client, db_session):
        """Test getting orders when none exist"""
        response = client.get("/orders/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_update_order_status(self, client, db_session, test_order):
        """Test updating order status"""
        status_update = {"status": "confirmed"}

        response = client.patch(f"/orders/{test_order.id}/status", json=status_update)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"
