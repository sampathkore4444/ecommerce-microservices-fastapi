import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from api_gateway.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_services():
    """Mock the external service calls"""
    with patch("api_gateway.main.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        yield mock_async_client
