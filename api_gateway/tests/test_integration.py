import pytest
from unittest.mock import patch, AsyncMock
import json


class TestAPIGatewayIntegration:
    def test_service_routing_integration(self, client, mock_services):
        """Test that gateway correctly routes to appropriate services"""

        # Mock different responses for different services
        def side_effect(url, **kwargs):
            mock_response = AsyncMock()
            if "user_service" in url:
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "service": "user_service",
                    "data": "user_data",
                }
            elif "product_service" in url:
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "service": "product_service",
                    "data": "product_data",
                }
            elif "order_service" in url:
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "service": "order_service",
                    "data": "order_data",
                }
            return mock_response

        mock_services.get.side_effect = side_effect
        mock_services.post.side_effect = side_effect

        # Test that each endpoint routes to correct service
        with patch("api_gateway.dependencies.httpx.AsyncClient") as mock_auth:
            mock_auth_client = AsyncMock()
            mock_auth.return_value.__aenter__.return_value = mock_auth_client
            mock_auth_client.get.return_value.status_code = 200
            mock_auth_client.get.return_value.json.return_value = {
                "id": "user-123",
                "username": "testuser",
            }

            # Test user service routing
            response = client.get(
                "/users/user-123", headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 200
            assert response.json()["service"] == "user_service"

            # Test product service routing
            response = client.get("/products/prod-123")
            assert response.status_code == 200
            assert response.json()["service"] == "product_service"

            # Test order service routing
            response = client.get(
                "/orders/order-123", headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 200
            assert response.json()["service"] == "order_service"

    def test_error_handling_integration(self, client, mock_services):
        """Test gateway error handling for different error types"""
        # Test 404 error propagation
        mock_services.get.return_value.status_code = 404
        mock_services.get.return_value.json.return_value = {
            "detail": "Resource not found in downstream service"
        }

        response = client.get("/products/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

        # Test 503 error propagation (service unavailable)
        mock_services.get.return_value.status_code = 503
        mock_services.get.return_value.json.return_value = {
            "detail": "Service temporarily unavailable"
        }

        response = client.get("/products/prod-123")
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"]

        # Test 400 error propagation (bad request)
        mock_services.post.return_value.status_code = 400
        mock_services.post.return_value.json.return_value = {
            "detail": "Invalid input data"
        }

        with patch("api_gateway.dependencies.httpx.AsyncClient") as mock_auth:
            mock_auth_client = AsyncMock()
            mock_auth.return_value.__aenter__.return_value = mock_auth_client
            mock_auth_client.get.return_value.status_code = 200
            mock_auth_client.get.return_value.json.return_value = {"id": "user-123"}

            response = client.post(
                "/users/",
                json={"invalid": "data"},
                headers={"Authorization": "Bearer token"},
            )
            assert response.status_code == 400
            assert "Invalid input" in response.json()["detail"]

    def test_request_forwarding_integration(self, client, mock_services):
        """Test that gateway correctly forwards request data"""
        test_user_data = {
            "username": "forwarduser",
            "email": "forward@example.com",
            "full_name": "Forward User",
            "password": "forwardpass123",
        }

        def assert_forwarded_data(url, json=None, **kwargs):
            # Verify that the gateway forwarded the correct data
            assert json is not None
            assert json["username"] == test_user_data["username"]
            assert json["email"] == test_user_data["email"]

            mock_response = AsyncMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "user-forward-123",
                **test_user_data,
            }
            return mock_response

        mock_services.post.side_effect = assert_forwarded_data

        with patch("api_gateway.dependencies.httpx.AsyncClient") as mock_auth:
            mock_auth_client = AsyncMock()
            mock_auth.return_value.__aenter__.return_value = mock_auth_client
            mock_auth_client.get.return_value.status_code = 200
            mock_auth_client.get.return_value.json.return_value = {"id": "user-123"}

            response = client.post(
                "/users/",
                json=test_user_data,
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["username"] == test_user_data["username"]

    def test_headers_forwarding_integration(self, client, mock_services):
        """Test that gateway handles headers correctly"""
        custom_headers = {
            "X-Custom-Header": "CustomValue",
            "User-Agent": "TestClient/1.0",
        }

        def assert_headers(url, headers=None, **kwargs):
            # Verify that certain headers are handled correctly
            assert headers is not None
            # Authorization header should be forwarded
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer valid.token"

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            return mock_response

        mock_services.get.side_effect = assert_headers

        with patch("api_gateway.dependencies.httpx.AsyncClient") as mock_auth:
            mock_auth_client = AsyncMock()
            mock_auth.return_value.__aenter__.return_value = mock_auth_client
            mock_auth_client.get.return_value.status_code = 200
            mock_auth_client.get.return_value.json.return_value = {"id": "user-123"}

            response = client.get(
                "/users/user-123",
                headers={"Authorization": "Bearer valid.token", **custom_headers},
            )

            assert response.status_code == 200

    def test_concurrent_requests_handling(self, client, mock_services):
        """Test that gateway can handle concurrent requests"""
        # This would be more comprehensive with async testing
        # For now, test that multiple sequential requests work correctly

        with patch("api_gateway.dependencies.httpx.AsyncClient") as mock_auth:
            mock_auth_client = AsyncMock()
            mock_auth.return_value.__aenter__.return_value = mock_auth_client
            mock_auth_client.get.return_value.status_code = 200
            mock_auth_client.get.return_value.json.return_value = {"id": "user-123"}

            # Make multiple requests sequentially
            responses = []
            for i in range(5):
                mock_services.get.return_value.json.return_value = {
                    "id": f"prod-{i}",
                    "name": f"Product {i}",
                    "price": 10.0 * (i + 1),
                }

                response = client.get(f"/products/prod-{i}")
                responses.append(response)

            # Verify all responses were successful
            for i, response in enumerate(responses):
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == f"prod-{i}"
                assert data["name"] == f"Product {i}"

    def test_gateway_metrics_endpoints(self, client):
        """Test gateway-specific metrics and monitoring endpoints"""
        # Test metrics endpoint (if implemented)
        response = client.get("/metrics")
        # This might return 404 if not implemented, or 200 if implemented
        assert response.status_code in [200, 404]

        # Test gateway metrics endpoint
        response = client.get("/metrics/gateway")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "api_gateway"
        assert "metrics" in data

    def test_cors_headers_integration(self, client):
        """Test that CORS headers are properly set"""
        # Test OPTIONS preflight request
        response = client.options(
            "/users/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )

        # Should return 200 for OPTIONS requests with CORS headers
        assert response.status_code == 200
        assert "access-control-allow-origin" in [h.lower() for h in response.headers]

        # Test regular request with Origin header
        response = client.get("/products/", headers={"Origin": "http://localhost:3000"})

        # Should include CORS headers in response
        assert "access-control-allow-origin" in [h.lower() for h in response.headers]
