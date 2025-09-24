# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from typing import Optional, List
# from pydantic import BaseModel
# import httpx

# # Import from shared package
# from shared.schemas import UserCreate, UserResponse
# from shared.schemas import ProductCreate, ProductResponse, ProductUpdate
# from shared.schemas import OrderCreate, OrderResponse, OrderStatus

# app = FastAPI(
#     title="API Gateway",
#     version="1.0.0",
#     description="Single entry point for all e-commerce microservices",
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Service URLs
# USER_SERVICE_URL = "http://localhost:8001"
# PRODUCT_SERVICE_URL = "http://localhost:8002"
# ORDER_SERVICE_URL = "http://localhost:8003"


# # User Service Routes
# @app.post("/users/")
# async def create_user(user_data: UserCreate):
#     async with httpx.AsyncClient() as client:
#         response = await client.post(f"{USER_SERVICE_URL}/users/", json=user_data)
#         return response.json()


# @app.get("/users/{user_id}")
# async def get_user(user_id: str):
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
#         return response.json()


# @app.get("/users/", response_model=List[UserResponse])
# async def get_users():
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{USER_SERVICE_URL}/users/")
#         return response.json()


# # Product Service Routes
# @app.post("/products/")
# async def create_product(product_data: ProductCreate):
#     async with httpx.AsyncClient() as client:
#         response = await client.post(
#             f"{PRODUCT_SERVICE_URL}/products/", json=product_data
#         )
#         return response.json()


# @app.get("/products/{product_id}")
# async def get_product(product_id: str):
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
#         return response.json()


# @app.get("/products/", response_model=List[ProductResponse])
# async def get_products():
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{PRODUCT_SERVICE_URL}/products/")
#         return response.json()


# @app.put("/products/{product_id}", response_model=ProductResponse)
# async def update_product(product_id: str, product_data: ProductUpdate):
#     async with httpx.AsyncClient() as client:
#         response = await client.put(
#             f"{PRODUCT_SERVICE_URL}/products/{product_id}", json=product_data
#         )
#         return response.json()


# @app.delete("/products/{product_id}")
# async def delete_product(product_id: str):
#     async with httpx.AsyncClient() as client:
#         response = await client.delete(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
#         return response.json()


# # Order Service Routes
# @app.post("/orders/", response_model=OrderResponse)
# async def create_order(order_data: OrderCreate):
#     async with httpx.AsyncClient() as client:
#         response = await client.post(f"{ORDER_SERVICE_URL}/orders/", json=order_data)
#         return response.json()


# @app.get("/orders/{order_id}")
# async def get_order(order_id: str):
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{ORDER_SERVICE_URL}/orders/{order_id}")
#         return response.json()


# @app.get("/orders/", response_model=List[OrderResponse])
# async def get_orders():
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{ORDER_SERVICE_URL}/orders/")
#         return response.json()


# @app.put("/orders/{order_id}")
# async def update_order(order_id: str, order_data: dict):
#     async with httpx.AsyncClient() as client:
#         response = await client.put(
#             f"{ORDER_SERVICE_URL}/orders/{order_id}", json=order_data
#         )
#         return response.json()


# @app.delete("/orders/{order_id}")
# async def delete_order(order_id: str):
#     async with httpx.AsyncClient() as client:
#         response = await client.delete(f"{ORDER_SERVICE_URL}/orders/{order_id}")
#         return response.json()


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=8000)


from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

from shared.schemas import UserCreate, UserResponse, ProductCreate, ProductResponse
from shared.schemas import OrderCreate, OrderResponse, LoginRequest
from .dependencies import verify_token

from .monitoring import monitor_app, track_downstream_request, track_downstream_error

# Load environment variables
load_dotenv()

app = FastAPI(
    title="E-commerce API Gateway",
    version="1.0.0",
    description="Single entry point for all e-commerce microservices",
)

# Service URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8002")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8003")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup monitoring
monitor_app(app, "api_gateway")


async def handle_service_response(response: httpx.Response):
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Resource not found")
    elif response.status_code >= 500:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    elif response.status_code >= 400:
        error_detail = response.json().get("detail", "Bad request")
        raise HTTPException(status_code=response.status_code, detail=error_detail)
    return response.json()


# Health check aggregator
@app.get("/health")
async def health_check():
    services = {
        "user_service": USER_SERVICE_URL,
        "product_service": PRODUCT_SERVICE_URL,
        "order_service": ORDER_SERVICE_URL,
    }

    status_report = {
        "gateway": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
    }

    for service_name, url in services.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                status_report["services"][service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                    "timestamp": datetime.now().isoformat(),
                }
                track_downstream_request(service_name, response.status_code)
        except Exception as e:
            status_report["services"][service_name] = {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            track_downstream_error(service_name)

    return status_report


# User Service Routes
@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_SERVICE_URL}/users/", json=user.dict())
        return await handle_service_response(response)


@app.get("/users/", response_model=list[UserResponse])
async def get_users(current_user: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/")
        return await handle_service_response(response)


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        return await handle_service_response(response)


# Authentication
@app.post("/token")
async def login(login_data: LoginRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_SERVICE_URL}/token",
            data={"username": login_data.username, "password": login_data.password},
        )
        return await handle_service_response(response)


# Product Service Routes
@app.post("/products/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate, current_user: dict = Depends(verify_token)
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PRODUCT_SERVICE_URL}/products/", json=product.dict()
        )
        return await handle_service_response(response)


@app.get("/products/", response_model=list[ProductResponse])
async def get_products(category: str = None, skip: int = 0, limit: int = 100):
    async with httpx.AsyncClient() as client:
        params = {"skip": skip, "limit": limit}
        if category:
            params["category"] = category

        response = await client.get(f"{PRODUCT_SERVICE_URL}/products/", params=params)
        return await handle_service_response(response)


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
        return await handle_service_response(response)


# Order Service Routes
@app.post("/orders/", response_model=OrderResponse)
async def create_order(order: OrderCreate, current_user: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{ORDER_SERVICE_URL}/orders/", json=order.dict())
        return await handle_service_response(response)


@app.get("/orders/", response_model=list[OrderResponse])
async def get_orders(user_id: str = None, current_user: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        params = {}
        if user_id:
            params["user_id"] = user_id

        response = await client.get(f"{ORDER_SERVICE_URL}/orders/", params=params)
        return await handle_service_response(response)


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, current_user: dict = Depends(verify_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ORDER_SERVICE_URL}/orders/{order_id}")
        return await handle_service_response(response)


@app.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str, status: dict, current_user: dict = Depends(verify_token)
):
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/status", json=status
        )
        return await handle_service_response(response)


@app.get("/")
async def root():
    return {
        "message": "E-commerce API Gateway",
        "version": "1.0.0",
        "services": {
            "user_service": USER_SERVICE_URL,
            "product_service": PRODUCT_SERVICE_URL,
            "order_service": ORDER_SERVICE_URL,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
