import pytest
from fastapi import HTTPException, Header
from unittest.mock import patch, AsyncMock

from api_gateway.dependencies import verify_token


class TestDependencies:
    @pytest.mark.asyncio
    async def test_verify_token_success(self, mock_token_verification):
        """Test successful token verification"""
        authorization = "Bearer valid.jwt.token"

        user = await verify_token(authorization)

        assert user is not None
        assert user["id"] == "user-123"
        assert user["username"] == "testuser"
        assert user["is_active"] == True

    @pytest.mark.asyncio
    async def test_verify_token_missing_header(self):
        """Test token verification with missing authorization header"""
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(None)

        assert exc_info.value.status_code == 401
        assert "Authorization header missing" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_invalid_format(self):
        """Test token verification with invalid header format"""
        with pytest.raises(HTTPException) as exc_info:
            await verify_token("InvalidFormat")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_token_user_service_unavailable(self):
        """Test token verification when user service is unavailable"""
        with patch("api_gateway.dependencies.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client

            # Mock service unavailable
            mock_async_client.get.return_value.status_code = 503

            with pytest.raises(HTTPException) as exc_info:
                await verify_token("Bearer some.token")

            assert exc_info.value.status_code == 503
            assert "User service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_invalid_token(self):
        """Test token verification with invalid token"""
        with patch("api_gateway.dependencies.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client

            # Mock invalid token response
            mock_async_client.get.return_value.status_code = 401

            with pytest.raises(HTTPException) as exc_info:
                await verify_token("Bearer invalid.token")

            assert exc_info.value.status_code == 401
            assert "Invalid token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_network_error(self):
        """Test token verification with network error"""
        with patch("api_gateway.dependencies.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client

            # Mock network error
            mock_async_client.get.side_effect = Exception("Network error")

            with pytest.raises(HTTPException) as exc_info:
                await verify_token("Bearer some.token")

            assert exc_info.value.status_code == 503
