import pytest
from datetime import datetime
from product_service.models import Product


class TestProductModel:
    def test_product_creation(self, db_session):
        """Test product model creation with all fields"""
        product = Product(
            name="Test Product",
            description="A test product description",
            price=29.99,
            category="electronics",
            stock=100,
        )
        db_session.add(product)
        db_session.commit()

        assert product.id is not None
        assert product.name == "Test Product"
        assert product.price == 29.99
        assert product.category == "electronics"
        assert product.stock == 100
        assert isinstance(product.created_at, datetime)
        assert product.created_at <= datetime.utcnow()

    def test_product_repr(self, db_session):
        """Test product string representation"""
        product = Product(
            name="Test Product",
            description="Test description",
            price=19.99,
            category="books",
            stock=50,
        )
        db_session.add(product)
        db_session.commit()

        assert "Test Product" in repr(product)
        assert "19.99" in repr(product)

    def test_product_default_values(self, db_session):
        """Test product model default values"""
        product = Product(
            name="Test Product",
            description="Test description",
            price=15.99,
            category="clothing",
            # stock should default to 0
        )
        db_session.add(product)
        db_session.commit()

        assert product.stock == 0
        assert product.created_at is not None
        assert product.updated_at is not None

    def test_product_price_validation(self, db_session):
        """Test that price must be positive"""
        with pytest.raises(ValueError):
            product = Product(
                name="Invalid Product",
                description="Test",
                price=-10.0,  # Negative price should be invalid
                category="electronics",
                stock=10,
            )
            db_session.add(product)
            db_session.commit()
