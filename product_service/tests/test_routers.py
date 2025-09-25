import pytest


class TestProductRoutes:
    def test_create_product_success(self, client, db_session):
        """Test successful product creation"""
        product_data = {
            "name": "New Product",
            "description": "A new test product",
            "price": 39.99,
            "category": "books",
            "stock": 50,
        }

        response = client.post("/products/", json=product_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Product"
        assert data["price"] == 39.99
        assert data["category"] == "books"

    def test_get_products_empty(self, client, db_session):
        """Test getting products when none exist"""
        response = client.get("/products/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_products_with_data(self, client, db_session, test_product):
        """Test getting products when data exists"""
        response = client.get("/products/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == test_product.name

    def test_get_product_by_id(self, client, db_session, test_product):
        """Test getting specific product by ID"""
        response = client.get(f"/products/{test_product.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_product.id
        assert data["name"] == test_product.name

    def test_update_product(self, client, db_session, test_product):
        """Test updating product information"""
        update_data = {"name": "Updated Product Name", "price": 49.99}

        response = client.put(f"/products/{test_product.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product Name"
        assert data["price"] == 49.99

    def test_delete_product(self, client, db_session, test_product):
        """Test product deletion"""
        response = client.delete(f"/products/{test_product.id}")

        assert response.status_code == 204

        # Verify product is actually deleted
        get_response = client.get(f"/products/{test_product.id}")
        assert get_response.status_code == 404
