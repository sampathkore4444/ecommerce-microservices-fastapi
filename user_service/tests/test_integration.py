import pytest
from fastapi.testclient import TestClient


class TestUserServiceIntegration:
    def test_full_user_workflow(self, client, db_session):
        """Test complete user registration and retrieval workflow"""
        # 1. Create a new user
        user_data = {
            "username": "integrationuser",
            "email": "integration@example.com",
            "full_name": "Integration Test User",
            "password": "integrationpass123",
        }

        create_response = client.post("/users/", json=user_data)
        assert create_response.status_code == 201
        created_user = create_response.json()

        # 2. Retrieve the created user
        get_response = client.get(f"/users/{created_user['id']}")
        assert get_response.status_code == 200
        retrieved_user = get_response.json()

        # 3. Verify data consistency
        assert created_user["id"] == retrieved_user["id"]
        assert created_user["username"] == retrieved_user["username"]
        assert created_user["email"] == retrieved_user["email"]

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "user_service"
