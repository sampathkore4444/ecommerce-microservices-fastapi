import pytest
from user_service.models import User


class TestUserModel:
    def test_user_creation(self, db_session):
        """Test user model creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashedpassword123",
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.is_active == True

    def test_user_repr(self, db_session):
        """Test user string representation"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashedpassword123",
        )
        db_session.add(user)
        db_session.commit()

        assert "testuser" in repr(user)
        assert "test@example.com" in repr(user)
