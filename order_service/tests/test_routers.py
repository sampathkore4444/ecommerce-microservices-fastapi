import pytest
from order_service.models import OrderStatus
from models import Order


class TestOrderRoutes:
    def test_create_order_success(self, client, db_session):
        """Test successful order creation"""
        order_data = {
            "items": [
                {"product_id": "prod-123", "quantity": 2, "price": 29.99},
                {"product_id": "prod-456", "quantity": 1, "price": 49.99},
            ],
            "total_amount": (2 * 29.99) + 49.99,  # 109.97
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == OrderStatus.PENDING
        assert data["total_amount"] == 109.97
        assert len(data["items"]) == 2
        assert data["user_id"] is not None

    def test_create_order_invalid_items(self, client, db_session):
        """Test order creation with invalid items data"""
        invalid_order_data = {
            "items": [
                {
                    "product_id": "prod-123",
                    "quantity": -1,  # Invalid negative quantity
                    "price": 29.99,
                }
            ],
            "total_amount": -29.99,  # Invalid negative amount
        }

        response = client.post("/orders/", json=invalid_order_data)

        # This should be 422 Unprocessable Entity due to Pydantic validation
        assert response.status_code == 422

    def test_get_orders_empty(self, client, db_session):
        """Test getting orders when none exist"""
        response = client.get("/orders/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_orders_with_data(self, client, db_session, test_order):
        """Test getting orders when data exists"""
        response = client.get("/orders/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == test_order.id
        assert data[0]["status"] == test_order.status

    def test_get_orders_filter_by_user(self, client, db_session):
        """Test filtering orders by user ID"""
        # Create orders for different users
        orders_data = [
            {
                "user_id": "user-1",
                "items": [{"product_id": "prod-1", "quantity": 1, "price": 10.0}],
                "total_amount": 10.0,
                "status": OrderStatus.PENDING,
            },
            {
                "user_id": "user-2",
                "items": [{"product_id": "prod-2", "quantity": 2, "price": 15.0}],
                "total_amount": 30.0,
                "status": OrderStatus.PENDING,
            },
            {
                "user_id": "user-1",  # Same user as first order
                "items": [{"product_id": "prod-3", "quantity": 1, "price": 20.0}],
                "total_amount": 20.0,
                "status": OrderStatus.CONFIRMED,
            },
        ]

        for order_data in orders_data:
            order = Order(**order_data)
            db_session.add(order)
        db_session.commit()

        # Filter by user-1
        response = client.get("/orders/?user_id=user-1")
        assert response.status_code == 200
        user_orders = response.json()

        assert len(user_orders) == 2
        for order in user_orders:
            assert order["user_id"] == "user-1"

    def test_get_order_by_id(self, client, db_session, test_order):
        """Test getting specific order by ID"""
        response = client.get(f"/orders/{test_order.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_order.id
        assert data["user_id"] == test_order.user_id
        assert data["total_amount"] == test_order.total_amount

    def test_get_order_not_found(self, client, db_session):
        """Test getting non-existent order"""
        response = client.get("/orders/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_order_status_valid(self, client, db_session, test_order):
        """Test valid order status update"""
        status_update = {"status": OrderStatus.CONFIRMED}

        response = client.patch(f"/orders/{test_order.id}/status", json=status_update)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == OrderStatus.CONFIRMED
        assert data["id"] == test_order.id

    def test_update_order_status_invalid(self, client, db_session, test_order):
        """Test order status update with invalid status"""
        invalid_status_update = {"status": "invalid_status"}

        response = client.patch(
            f"/orders/{test_order.id}/status", json=invalid_status_update
        )

        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    def test_update_order_status_not_found(self, client, db_session):
        """Test status update for non-existent order"""
        status_update = {"status": OrderStatus.CONFIRMED}

        response = client.patch("/orders/non-existent-id/status", json=status_update)

        assert response.status_code == 404

    def test_delete_order_success(self, client, db_session, test_order):
        """Test successful order deletion"""
        response = client.delete(f"/orders/{test_order.id}")

        assert response.status_code == 204

        # Verify order is actually deleted
        get_response = client.get(f"/orders/{test_order.id}")
        assert get_response.status_code == 404

    def test_delete_order_not_found(self, client, db_session):
        """Test deletion of non-existent order"""
        response = client.delete("/orders/non-existent-id")

        assert response.status_code == 404

    def test_get_user_orders(self, client, db_session):
        """Test getting orders for specific user"""
        # Create orders for a specific user
        user_id = "test-user-123"
        for i in range(3):
            order = Order(
                user_id=user_id,
                items=[
                    {"product_id": f"prod-{i}", "quantity": 1, "price": 10.0 * (i + 1)}
                ],
                total_amount=10.0 * (i + 1),
                status=OrderStatus.PENDING,
            )
            db_session.add(order)
        db_session.commit()

        response = client.get(f"/orders/user/{user_id}/orders")
        assert response.status_code == 200
        user_orders = response.json()

        assert len(user_orders) == 3
        for order in user_orders:
            assert order["user_id"] == user_id
