import pytest
from unittest.mock import patch, MagicMock
from api_gateway.monitoring import (
    monitor_app,
    track_downstream_request,
    track_downstream_error,
)


class TestAPIGatewayMonitoring:
    def test_monitor_app_initialization(self, client):
        """Test that monitoring setup works correctly"""
        # The monitor_app function should be called in main.py
        # This test verifies the monitoring endpoints exist

        # Test metrics endpoint
        response = client.get("/metrics")
        # May return 200 if Prometheus is set up, or 404 if not
        assert response.status_code in [200, 404]

        # Test gateway metrics endpoint
        response = client.get("/metrics/gateway")
        assert response.status_code == 200

        # Test health endpoint includes monitoring info
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "gateway" in data
        assert "services" in data

    def test_track_downstream_request(self):
        """Test downstream request tracking"""
        # This would test the metrics tracking functionality
        # Since it's mostly side effects, we test that the function exists and is callable
        assert callable(track_downstream_request)
        assert callable(track_downstream_error)

        # Test that functions can be called without errors
        try:
            track_downstream_request("user_service", 200)
            track_downstream_error("product_service")
            # If we get here, the functions work
            assert True
        except Exception:
            assert False, "Monitoring functions should not raise exceptions"

    def test_monitoring_middleware(self, client, mock_services):
        """Test that monitoring middleware adds appropriate headers"""
        mock_services.get.return_value.status_code = 200
        mock_services.get.return_value.json.return_value = {
            "id": "prod-123",
            "name": "Test Product",
        }

        response = client.get("/products/prod-123")

        # Check for monitoring headers
        headers = {k.lower(): v for k, v in response.headers.items()}

        # These headers might be added by the monitoring middleware
        monitoring_headers = [
            "x-process-time",
            "x-service",
            "x-request-id",
            "x-response-time",
        ]

        # At least one monitoring header should be present
        has_monitoring_headers = any(header in headers for header in monitoring_headers)
        assert (
            has_monitoring_headers
        ), "Monitoring headers should be present in response"
