from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
import httpx

app = FastAPI(
    title="API Gateway",
    version="1.0.0",
    description="Single entry point for all e-commerce microservices",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
USER_SERVICE_URL = "http://localhost:8001"
PRODUCT_SERVICE_URL = "http://localhost:8002"
ORDER_SERVICE_URL = "http://localhost:8003"


# User Service Routes
@app.post("/users/")
async def create_user(user_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_SERVICE_URL}/users/", json=user_data)
        return response.json()


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        return response.json()


@app.get("/users/")
async def get_users():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/")
        return response.json()


# Product Service Routes
@app.post("/products/")
async def create_product(product_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PRODUCT_SERVICE_URL}/products/", json=product_data
        )
        return response.json()


@app.get("/products/{product_id}")
async def get_product(product_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
        return response.json()


@app.get("/products/")
async def get_products():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PRODUCT_SERVICE_URL}/products/")
        return response.json()


@app.put("/products/{product_id}")
async def update_product(product_id: str, product_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}", json=product_data
        )
        return response.json()


@app.delete("/products/{product_id}")
async def delete_product(product_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
        return response.json()


# Order Service Routes
@app.post("/orders/")
async def create_order(order_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{ORDER_SERVICE_URL}/orders/", json=order_data)
        return response.json()


@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ORDER_SERVICE_URL}/orders/{order_id}")
        return response.json()


@app.get("/orders/")
async def get_order():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ORDER_SERVICE_URL}/orders/")
        return response.json()


@app.put("/orders/{order_id}")
async def update_order(order_id: str, order_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{ORDER_SERVICE_URL}/orders/{order_id}", json=order_data
        )
        return response.json()


@app.delete("/orders/{order_id}")
async def delete_order(order_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{ORDER_SERVICE_URL}/orders/{order_id}")
        return response.json()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
