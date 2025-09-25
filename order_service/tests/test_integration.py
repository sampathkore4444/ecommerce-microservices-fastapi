import pytest
from fastapi.testclient import TestClient
from order_service.models import OrderStatus
from models import Order


class TestOrderServiceIntegration:
    def test_complete_order_workflow(self, client, db_session):
        """Test complete order lifecycle workflow"""
        # 1. Create an order
        order_data = {
            "items": [
                {"product_id": "prod-integration-1", "quantity": 3, "price": 15.99},
                {"product_id": "prod-integration-2", "quantity": 1, "price": 99.99},
            ],
            "total_amount": (3 * 15.99) + 99.99,  # 147.96
        }

        create_response = client.post("/orders/", json=order_data)
        assert create_response.status_code == 201
        created_order = create_response.json()
        order_id = created_order["id"]

        # Verify initial status
        assert created_order["status"] == OrderStatus.PENDING
        assert len(created_order["items"]) == 2
        assert created_order["total_amount"] == 147.96

        # 2. Get the order
        get_response = client.get(f"/orders/{order_id}")
        assert get_response.status_code == 200
        retrieved_order = get_response.json()

        # Verify data consistency
        assert created_order["id"] == retrieved_order["id"]
        assert created_order["total_amount"] == retrieved_order["total_amount"]

        # 3. Update status to confirmed
        confirm_response = client.patch(
            f"/orders/{order_id}/status", json={"status": OrderStatus.CONFIRMED}
        )
        assert confirm_response.status_code == 200
        confirmed_order = confirm_response.json()
        assert confirmed_order["status"] == OrderStatus.CONFIRMED

        # 4. Update status to shipped
        ship_response = client.patch(
            f"/orders/{order_id}/status", json={"status": OrderStatus.SHIPPED}
        )
        assert ship_response.status_code == 200
        shipped_order = ship_response.json()
        assert shipped_order["status"] == OrderStatus.SHIPPED

        # 5. Update status to delivered
        deliver_response = client.patch(
            f"/orders/{order_id}/status", json={"status": OrderStatus.DELIVERED}
        )
        assert deliver_response.status_code == 200
        delivered_order = deliver_response.json()
        assert delivered_order["status"] == OrderStatus.DELIVERED

        # 6. Verify order history through multiple GETs
        final_get_response = client.get(f"/orders/{order_id}")
        assert final_get_response.status_code == 200
        final_order = final_get_response.json()
        assert final_order["status"] == OrderStatus.DELIVERED

        # 7. Delete the order
        delete_response = client.delete(f"/orders/{order_id}")
        assert delete_response.status_code == 204

        # 8. Verify order is gone
        final_check_response = client.get(f"/orders/{order_id}")
        assert final_check_response.status_code == 404

    def test_order_filtering_integration(self, client, db_session):
        """Test complex order filtering scenarios"""
        # Create orders with different statuses and users
        test_orders = [
            {"user_id": "user-a", "status": OrderStatus.PENDING, "amount": 50.0},
            {"user_id": "user-a", "status": OrderStatus.CONFIRMED, "amount": 75.0},
            {"user_id": "user-b", "status": OrderStatus.PENDING, "amount": 100.0},
            {"user_id": "user-b", "status": OrderStatus.SHIPPED, "amount": 150.0},
            {"user_id": "user-c", "status": OrderStatus.DELIVERED, "amount": 200.0},
        ]

        for order_data in test_orders:
            order = Order(
                user_id=order_data["user_id"],
                items=[
                    {
                        "product_id": "prod-1",
                        "quantity": 1,
                        "price": order_data["amount"],
                    }
                ],
                total_amount=order_data["amount"],
                status=order_data["status"],
            )
            db_session.add(order)
        db_session.commit()

        # Test filtering by user
        user_a_orders = client.get("/orders/?user_id=user-a").json()
        assert len(user_a_orders) == 2
        for order in user_a_orders:
            assert order["user_id"] == "user-a"

        # Test filtering by status
        pending_orders = client.get("/orders/?status=pending").json()
        assert len(pending_orders) == 2
        for order in pending_orders:
            assert order["status"] == OrderStatus.PENDING

        # Test combined filtering (user + status)
        user_b_pending = client.get("/orders/?user_id=user-b&status=pending").json()
        assert len(user_b_pending) == 1
        assert user_b_pending[0]["user_id"] == "user-b"
        assert user_b_pending[0]["status"] == OrderStatus.PENDING

    def test_order_pagination_integration(self, client, db_session):
        """Test order pagination with real data"""
        # Create 25 test orders
        for i in range(25):
            order = Order(
                user_id=f"user-{i % 5}",  # 5 different users
                items=[
                    {"product_id": f"prod-{i}", "quantity": 1, "price": 10.0 * (i + 1)}
                ],
                total_amount=10.0 * (i + 1),
                status=OrderStatus.PENDING,
            )
            db_session.add(order)
        db_session.commit()

        # Test pagination
        page1 = client.get("/orders/?skip=0&limit=10").json()
        assert len(page1) == 10

        page2 = client.get("/orders/?skip=10&limit=10").json()
        assert len(page2) == 10

        page3 = client.get("/orders/?skip=20&limit=10").json()
        assert len(page3) == 5  # Only 5 left

        # Verify no overlap between pages
        page1_ids = {order["id"] for order in page1}
        page2_ids = {order["id"] for order in page2}
        page3_ids = {order["id"] for order in page3}

        assert page1_ids.isdisjoint(page2_ids)
        assert page1_ids.isdisjoint(page3_ids)
        assert page2_ids.isdisjoint(page3_ids)

    def test_health_checks(self, client):
        """Test order service health endpoints"""
        # Basic health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "order_service"

        # Detailed health check
        detailed_response = client.get("/health/detailed")
        assert detailed_response.status_code == 200
        detailed_data = detailed_response.json()
        assert detailed_data["service"] == "order_service"
        assert "database" in detailed_data
        assert "timestamp" in detailed_data
