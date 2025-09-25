import pytest
from unittest.mock import patch


class TestAPIGateway:
    def test_health_check(self, client, mock_services):
        """Test gateway health check"""
        # Mock service responses
        mock_services.get.return_value.status_code = 200
        mock_services.get.return_value.json.return_value = {
            "status": "healthy",
            "service": "user_service",
        }

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["gateway"] == "healthy"
        assert "user_service" in data["services"]

    def test_user_creation_through_gateway(self, client, mock_services):
        """Test user creation routed through gateway"""
        user_data = {
            "username": "gatewayuser",
            "email": "gateway@example.com",
            "full_name": "Gateway User",
            "password": "gatewaypass123",
        }

        # Mock user service response
        mock_services.post.return_value.status_code = 201
        mock_services.post.return_value.json.return_value = {
            "id": "user-gateway-123",
            "username": "gatewayuser",
            "email": "gateway@example.com",
            "full_name": "Gateway User",
            "is_active": True,
        }

        response = client.post("/users/", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "gatewayuser"

    def test_service_unavailable(self, client, mock_services):
        """Test gateway handling of unavailable services"""
        # Mock service failure
        mock_services.get.return_value.status_code = 503

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["services"]["user_service"]["status"] == "unhealthy"
