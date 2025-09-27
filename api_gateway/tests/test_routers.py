import pytest
from unittest.mock import patch


class TestAPIGatewayRoutes:
    def test_root_endpoint(self, client):
        """Test API Gateway root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "E-commerce API Gateway"
        assert "version" in data
        assert "services" in data
        assert "monitoring" in data

    def test_health_check_success(self, client, mock_services):
        """Test health check with all services healthy"""
        # Mock successful health checks from all services
        mock_services.get.return_value.json.return_value = {
            "status": "healthy",
            "service": "user_service",
        }
        mock_services.get.return_value.elapsed.total_seconds.return_value = 0.1

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["gateway"] == "healthy"
        assert "services" in data
        assert data["services"]["user_service"]["status"] == "healthy"
        assert data["services"]["product_service"]["status"] == "healthy"
        assert data["services"]["order_service"]["status"] == "healthy"

    def test_health_check_service_unavailable(self, client, mock_failing_services):
        """Test health check when services are unavailable"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["gateway"] == "healthy"
        assert data["services"]["user_service"]["status"] == "unhealthy"
        assert "error" in data["services"]["user_service"]

    def test_create_user_success(self, client, mock_services, mock_token_verification):
        """Test user creation through gateway"""
        user_data = {
            "username": "gatewayuser",
            "email": "gateway@example.com",
            "full_name": "Gateway User",
            "password": "gatewaypass123",
        }

        # Mock user service response
        mock_services.post.return_value.json.return_value = {
            "id": "user-gateway-123",
            "username": "gatewayuser",
            "email": "gateway@example.com",
            "full_name": "Gateway User",
            "is_active": True,
        }

        response = client.post(
            "/users/", json=user_data, headers={"Authorization": "Bearer valid.token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "gatewayuser"
        assert data["email"] == "gateway@example.com"
        assert "password" not in data

    def test_create_user_unauthorized(self, client):
        """Test user creation without authentication"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "testpass123",
        }

        response = client.post("/users/", json=user_data)
        # Should be 401 Unauthorized without token
        assert response.status_code == 401

    def test_get_users_success(self, client, mock_services, mock_token_verification):
        """Test getting users through gateway"""
        # Mock user service response
        mock_services.get.return_value.json.return_value = [
            {
                "id": "user-1",
                "username": "user1",
                "email": "user1@example.com",
                "full_name": "User One",
                "is_active": True,
            },
            {
                "id": "user-2",
                "username": "user2",
                "email": "user2@example.com",
                "full_name": "User Two",
                "is_active": True,
            },
        ]

        response = client.get(
            "/users/", headers={"Authorization": "Bearer valid.token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["username"] == "user1"
        assert data[1]["username"] == "user2"

    def test_get_user_by_id_success(
        self, client, mock_services, mock_token_verification
    ):
        """Test getting specific user by ID through gateway"""
        user_id = "user-123"

        mock_services.get.return_value.json.return_value = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
        }

        response = client.get(
            f"/users/{user_id}", headers={"Authorization": "Bearer valid.token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == "testuser"

    def test_get_user_not_found(self, client, mock_services, mock_token_verification):
        """Test getting non-existent user through gateway"""
        user_id = "non-existent-user"

        # Mock 404 response from user service
        mock_services.get.return_value.status_code = 404
        mock_services.get.return_value.json.return_value = {"detail": "User not found"}

        response = client.get(
            f"/users/{user_id}", headers={"Authorization": "Bearer valid.token"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_create_product_success(
        self, client, mock_services, mock_token_verification
    ):
        """Test product creation through gateway"""
        product_data = {
            "name": "Gateway Product",
            "description": "Product created through gateway",
            "price": 99.99,
            "category": "electronics",
            "stock": 50,
        }

        mock_services.post.return_value.json.return_value = {
            "id": "prod-gateway-123",
            "name": "Gateway Product",
            "description": "Product created through gateway",
            "price": 99.99,
            "category": "electronics",
            "stock": 50,
        }

        response = client.post(
            "/products/",
            json=product_data,
            headers={"Authorization": "Bearer valid.token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Gateway Product"
        assert data["price"] == 99.99

    def test_get_products_success(self, client, mock_services):
        """Test getting products through gateway (no auth required)"""
        mock_services.get.return_value.json.return_value = [
            {
                "id": "prod-1",
                "name": "Product One",
                "description": "First product",
                "price": 19.99,
                "category": "electronics",
                "stock": 10,
            },
            {
                "id": "prod-2",
                "name": "Product Two",
                "description": "Second product",
                "price": 29.99,
                "category": "books",
                "stock": 20,
            },
        ]

        response = client.get("/products/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Product One"
        assert data[1]["name"] == "Product Two"

    def test_get_products_with_filters(self, client, mock_services):
        """Test getting products with category filter through gateway"""
        mock_services.get.return_value.json.return_value = [
            {
                "id": "prod-1",
                "name": "Electronics Product",
                "description": "An electronics item",
                "price": 199.99,
                "category": "electronics",
                "stock": 5,
            }
        ]

        response = client.get("/products/?category=electronics")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "electronics"

    def test_get_product_by_id_success(self, client, mock_services):
        """Test getting specific product by ID through gateway"""
        product_id = "prod-123"

        mock_services.get.return_value.json.return_value = {
            "id": product_id,
            "name": "Test Product",
            "description": "A test product",
            "price": 49.99,
            "category": "test",
            "stock": 100,
        }

        response = client.get(f"/products/{product_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == "Test Product"

    def test_create_order_success(self, client, mock_services, mock_token_verification):
        """Test order creation through gateway"""
        order_data = {
            "items": [{"product_id": "prod-123", "quantity": 2, "price": 29.99}],
            "total_amount": 59.98,
        }

        mock_services.post.return_value.json.return_value = {
            "id": "order-gateway-123",
            "user_id": "user-123",
            "items": order_data["items"],
            "total_amount": 59.98,
            "status": "pending",
        }

        response = client.post(
            "/orders/", json=order_data, headers={"Authorization": "Bearer valid.token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "order-gateway-123"
        assert data["total_amount"] == 59.98
        assert data["status"] == "pending"

    def test_get_orders_success(self, client, mock_services, mock_token_verification):
        """Test getting orders through gateway"""
        mock_services.get.return_value.json.return_value = [
            {
                "id": "order-1",
                "user_id": "user-123",
                "items": [{"product_id": "prod-1", "quantity": 1, "price": 10.0}],
                "total_amount": 10.0,
                "status": "pending",
            },
            {
                "id": "order-2",
                "user_id": "user-123",
                "items": [{"product_id": "prod-2", "quantity": 2, "price": 15.0}],
                "total_amount": 30.0,
                "status": "confirmed",
            },
        ]

        response = client.get(
            "/orders/", headers={"Authorization": "Bearer valid.token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["status"] == "pending"
        assert data[1]["status"] == "confirmed"

    def test_get_orders_with_user_filter(
        self, client, mock_services, mock_token_verification
    ):
        """Test getting orders with user filter through gateway"""
        user_id = "user-456"

        mock_services.get.return_value.json.return_value = [
            {
                "id": "order-456",
                "user_id": user_id,
                "items": [{"product_id": "prod-1", "quantity": 1, "price": 20.0}],
                "total_amount": 20.0,
                "status": "shipped",
            }
        ]

        response = client.get(
            f"/orders/?user_id={user_id}",
            headers={"Authorization": "Bearer valid.token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == user_id

    def test_get_order_by_id_success(
        self, client, mock_services, mock_token_verification
    ):
        """Test getting specific order by ID through gateway"""
        order_id = "order-123"

        mock_services.get.return_value.json.return_value = {
            "id": order_id,
            "user_id": "user-123",
            "items": [{"product_id": "prod-1", "quantity": 1, "price": 25.0}],
            "total_amount": 25.0,
            "status": "delivered",
        }

        response = client.get(
            f"/orders/{order_id}", headers={"Authorization": "Bearer valid.token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["status"] == "delivered"

    def test_update_order_status_success(
        self, client, mock_services, mock_token_verification
    ):
        """Test updating order status through gateway"""
        order_id = "order-123"
        status_update = {"status": "confirmed"}

        mock_services.patch.return_value.json.return_value = {
            "id": order_id,
            "user_id": "user-123",
            "items": [{"product_id": "prod-1", "quantity": 1, "price": 25.0}],
            "total_amount": 25.0,
            "status": "confirmed",
        }

        response = client.patch(
            f"/orders/{order_id}/status",
            json=status_update,
            headers={"Authorization": "Bearer valid.token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"

    def test_login_success(self, client, mock_services):
        """Test user login through gateway"""
        login_data = {"username": "testuser", "password": "testpassword"}

        mock_services.post.return_value.json.return_value = {
            "access_token": "jwt.token.here",
            "token_type": "bearer",
        }

        response = client.post("/token", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
