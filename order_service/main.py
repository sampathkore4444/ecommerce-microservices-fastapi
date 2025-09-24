# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import List, Optional
# import uuid
# from datetime import datetime
# from enum import Enum

# from shared.schemas import OrderCreate, OrderResponse, OrderStatus


# app = FastAPI(title="Order Service", version="1.0.0")

# # In-memory database
# orders_db = {}


# # Enums
# class OrderStatus(str, Enum):
#     PENDING = "pending"
#     CONFIRMED = "confirmed"
#     SHIPPED = "shipped"
#     DELIVERED = "delivered"
#     CANCELLED = "cancelled"


# # Models
# class OrderItem(BaseModel):
#     product_id: str
#     quantity: int
#     price: float


# class OrderCreate(BaseModel):
#     user_id: str
#     items: List[OrderItem]
#     total_amount: float


# class OrderResponse(BaseModel):
#     id: str
#     user_id: str
#     items: List[OrderItem]
#     total_amount: float
#     status: OrderStatus
#     created_at: datetime


# # Routes
# @app.post("/orders/", response_model=OrderResponse)
# async def create_order(order_data: OrderCreate):
#     order_id = str(uuid.uuid4())

#     order_data = {
#         "id": order_data,
#         "user_id": order_data.user_id,
#         "items": [item.model_dump() for item in order_data.items],
#         "total_amount": order_data.total_amount,
#         "status": OrderStatus.PENDING,
#         "created_at": datetime.now(),
#     }

#     # save to database
#     orders_db[order_id] = order_data

#     return order_data


# @app.get("/orders/", response_model=List[OrderResponse])
# async def get_all_orders(user_id: Optional[str] = None):
#     if user_id:
#         custom_orders = []
#         for order in orders_db.values():
#             if order["user_id"] == user_id:
#                 custom_orders.append(order)
#         return custom_orders
#     else:
#         return list(orders_db.values())


# @app.get("/orders/{order_id}", response_model=OrderResponse)
# async def get_order(order_id: str):
#     if order_id in orders_db:
#         return orders_db[order_id]
#     else:
#         raise HTTPException(status_code=404, detail=f"Order - {order_id} not found")


# @app.put("/orders/{order_id}", response_model=OrderResponse)
# async def update_order_status(order_id: str, new_status: str):
#     if order_id in orders_db:
#         order_data = orders_db[order_id]

#         # update the above order data with the new data receieved in the api (status)
#         order_data["status"] = new_status

#         # save back to database
#         orders_db[order_id] = order_data

#         return order_data

#     else:
#         raise HTTPException(status_code=404, detail=f"Order-{order_id} not found")


# @app.delete("/orders/{order_id}", status_code=204)
# async def delete_order(order_id: str):
#     if order_id in orders_db:
#         del orders_db[order_id]
#     else:
#         raise HTTPException(status_code=404, detail=f"Order {order_id} not found")


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app=app, host="0.0.0.0.", port=8003)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime

from .database import Base, engine
from .routers import orders

from monitoring import monitor_app, track_order_creation, track_order_completion

# Load environment variables
load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Order Service", version="1.0.0", description="Order management service"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(orders.router)

# Setup monitoring
monitor_app(app, "order_service")


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "order_service",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependency verification"""
    try:
        from database import SessionLocal

        db = SessionLocal()
        db.execute("SELECT 1")  # Test database connection
        db.close()

        return {
            "status": "healthy",
            "service": "order_service",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "order_service",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.get("/")
async def root():
    return {
        "message": "Order Service is running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "business_metrics": "/metrics/business",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
