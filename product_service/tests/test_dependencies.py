import pytest
from fastapi import HTTPException
from product_service.dependencies import get_product_or_404
from product_service.models import Product


class TestProductDependencies:
    def test_get_product_or_404_found(self, db_session, test_product):
        """Test dependency returns product when exists"""
        product = get_product_or_404(test_product.id, db_session)

        assert product is not None
        assert product.id == test_product.id
        assert product.name == test_product.name

    def test_get_product_or_404_not_found(self, db_session):
        """Test dependency raises 404 when product not found"""
        with pytest.raises(HTTPException) as exc_info:
            get_product_or_404("non-existent-id", db_session)

        assert exc_info.value.status_code == 404
        assert "Product not found" in exc_info.value.detail

    def test_get_product_or_404_empty_string(self, db_session):
        """Test dependency with empty string ID"""
        with pytest.raises(HTTPException) as exc_info:
            get_product_or_404("", db_session)

        assert exc_info.value.status_code == 404

    def test_get_product_or_404_none_id(self, db_session):
        """Test dependency with None ID"""
        with pytest.raises(HTTPException) as exc_info:
            get_product_or_404(None, db_session)

        assert exc_info.value.status_code == 404
