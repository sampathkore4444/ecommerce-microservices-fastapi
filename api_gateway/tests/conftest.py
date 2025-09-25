import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import os

from api_gateway.main import app
from api_gateway.dependencies import verify_token


@pytest.fixture(scope="module")
def client():
    """Create test client for API Gateway"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for external service calls"""
    with patch("api_gateway.main.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        yield mock_async_client


@pytest.fixture
def mock_services(mock_httpx_client):
    """Mock all external services with successful responses"""
    # Mock successful responses from all services
    mock_httpx_client.post.return_value.status_code = 201
    mock_httpx_client.get.return_value.status_code = 200
    mock_httpx_client.put.return_value.status_code = 200
    mock_httpx_client.patch.return_value.status_code = 200
    mock_httpx_client.delete.return_value.status_code = 204

    return mock_httpx_client


@pytest.fixture
def valid_token():
    """Return a valid JWT token for testing"""
    return "valid.jwt.token.here"


@pytest.fixture
def mock_token_verification():
    """Mock token verification to return a user"""
    with patch("api_gateway.dependencies.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client

        # Mock successful token verification
        mock_async_client.get.return_value.status_code = 200
        mock_async_client.get.return_value.json.return_value = {
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
        }

        yield mock_async_client


@pytest.fixture
def mock_failing_services(mock_httpx_client):
    """Mock external services with failures"""
    mock_httpx_client.get.return_value.status_code = 503
    mock_httpx_client.post.return_value.status_code = 500
    return mock_httpx_client
