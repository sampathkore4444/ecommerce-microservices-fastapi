import pytest
from pydantic import ValidationError
from shared.schemas import (
    UserCreate,
    UserResponse,
    ProductCreate,
    ProductResponse,
    OrderCreate,
)


class TestUserSchemas:
    def test_user_create_valid(self):
        """Test valid user creation"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "securepassword123",
        }
        user = UserCreate(**user_data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_user_create_invalid_email(self):
        """Test user creation with invalid email"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="invalid-email",
                full_name="Test User",
                password="password123",
            )

    def test_user_create_missing_field(self):
        """Test user creation with missing required field"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                # missing full_name and password
            )


class TestProductSchemas:
    def test_product_create_valid(self):
        """Test valid product creation"""
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "price": 29.99,
            "category": "electronics",
            "stock": 100,
        }
        product = ProductCreate(**product_data)
        assert product.name == "Test Product"
        assert product.price == 29.99

    def test_product_create_invalid_price(self):
        """Test product creation with invalid price"""
        with pytest.raises(ValidationError):
            ProductCreate(
                name="Test Product",
                description="A test product",
                price=-10.0,  # Negative price
                category="electronics",
                stock=100,
            )


class TestOrderSchemas:
    def test_order_create_valid(self):
        """Test valid order creation"""
        order_data = {
            "items": [{"product_id": "prod-123", "quantity": 2, "price": 29.99}],
            "total_amount": 59.98,
        }
        order = OrderCreate(**order_data)
        assert len(order.items) == 1
        assert order.total_amount == 59.98
