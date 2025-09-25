import pytest
from fastapi.testclient import TestClient


class TestProductServiceIntegration:
    def test_full_product_lifecycle(self, client, db_session):
        """Test complete product CRUD lifecycle"""
        # 1. Create a product
        product_data = {
            "name": "Integration Test Product",
            "description": "Product for integration testing",
            "price": 49.99,
            "category": "integration-test",
            "stock": 25,
        }

        create_response = client.post("/products/", json=product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        product_id = created_product["id"]

        # 2. Retrieve the product
        get_response = client.get(f"/products/{product_id}")
        assert get_response.status_code == 200
        retrieved_product = get_response.json()

        # Verify data consistency
        assert created_product["id"] == retrieved_product["id"]
        assert created_product["name"] == retrieved_product["name"]
        assert created_product["price"] == retrieved_product["price"]

        # 3. Update the product
        update_data = {
            "name": "Updated Integration Product",
            "price": 59.99,
            "stock": 30,
        }

        update_response = client.put(f"/products/{product_id}", json=update_data)
        assert update_response.status_code == 200
        updated_product = update_response.json()

        assert updated_product["name"] == "Updated Integration Product"
        assert updated_product["price"] == 59.99
        assert updated_product["stock"] == 30

        # 4. Partial update (PATCH)
        patch_data = {"stock": 15}
        patch_response = client.patch(f"/products/{product_id}/stock", json=patch_data)
        assert patch_response.status_code == 200
        patched_product = patch_response.json()

        assert patched_product["stock"] == 15
        assert patched_product["name"] == "Updated Integration Product"  # Unchanged

        # 5. Delete the product
        delete_response = client.delete(f"/products/{product_id}")
        assert delete_response.status_code == 204

        # 6. Verify product is gone
        final_get_response = client.get(f"/products/{product_id}")
        assert final_get_response.status_code == 404

    def test_product_filtering(self, client, db_session):
        """Test product filtering by category"""
        # Create products in different categories
        products_data = [
            {
                "name": "Electronics Product",
                "description": "An electronics item",
                "price": 299.99,
                "category": "electronics",
                "stock": 10,
            },
            {
                "name": "Book Product",
                "description": "A book item",
                "price": 19.99,
                "category": "books",
                "stock": 50,
            },
            {
                "name": "Another Electronics Product",
                "description": "Another electronics item",
                "price": 399.99,
                "category": "electronics",
                "stock": 5,
            },
        ]

        for product_data in products_data:
            response = client.post("/products/", json=product_data)
            assert response.status_code == 201

        # Test filtering by electronics category
        electronics_response = client.get("/products/?category=electronics")
        assert electronics_response.status_code == 200
        electronics_products = electronics_response.json()

        assert len(electronics_products) == 2
        for product in electronics_products:
            assert product["category"] == "electronics"

        # Test filtering by books category
        books_response = client.get("/products/?category=books")
        assert books_response.status_code == 200
        books_products = books_response.json()

        assert len(books_products) == 1
        assert books_products[0]["category"] == "books"

        # Test non-existent category
        empty_response = client.get("/products/?category=non-existent")
        assert empty_response.status_code == 200
        assert len(empty_response.json()) == 0

    def test_product_pagination(self, client, db_session):
        """Test product pagination functionality"""
        # Create multiple products
        for i in range(15):
            product_data = {
                "name": f"Product {i}",
                "description": f"Description for product {i}",
                "price": 10.0 + i,
                "category": "pagination-test",
                "stock": i * 5,
            }
            response = client.post("/products/", json=product_data)
            assert response.status_code == 201

        # Test pagination with skip and limit
        page1_response = client.get("/products/?skip=0&limit=5")
        assert page1_response.status_code == 200
        page1_products = page1_response.json()
        assert len(page1_products) == 5

        page2_response = client.get("/products/?skip=5&limit=5")
        assert page2_response.status_code == 200
        page2_products = page2_response.json()
        assert len(page2_products) == 5

        # Verify different products on each page
        page1_ids = {p["id"] for p in page1_products}
        page2_ids = {p["id"] for p in page2_products}
        assert page1_ids.isdisjoint(page2_ids)  # No overlap

    def test_health_check_integration(self, client):
        """Test health check integration"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "product_service"

        # Test detailed health check
        detailed_response = client.get("/health/detailed")
        assert detailed_response.status_code == 200
        detailed_data = detailed_response.json()
        assert detailed_data["service"] == "product_service"
        assert "database" in detailed_data
