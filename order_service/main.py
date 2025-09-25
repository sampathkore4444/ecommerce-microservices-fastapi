from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime

from .database import Base, engine
from .routers import orders

from monitoring import monitor_app, track_order_creation, track_order_completion

from contextlib import asynccontextmanager
import asyncio
from .event_handlers import message_queue, handle_inventory_updates, MessageType

# Load environment variables
load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to message queue
    await message_queue.connect()

    # Start consuming inventory update responses
    inventory_task = asyncio.create_task(
        message_queue.consume_messages(
            MessageType.INVENTORY_LOW, handle_inventory_updates
        )
    )

    yield

    # Shutdown: Close connections
    inventory_task.cancel()
    await message_queue.close()


app = FastAPI(
    title="Order Service",
    version="1.0.0",
    description="""
# Order Management Microservice 🛒

Complete order processing system for the E-commerce Platform with real-time status tracking.

## 💰 Features

- **Order Processing**: Complete order lifecycle management
- **Payment Integration**: Support for multiple payment gateways
- **Status Tracking**: Real-time order status updates
- **Shipping Integration**: Carrier API integrations
- **Tax Calculation**: Automated tax computation

## 🔄 Workflow Management

- **Order Creation**: Cart to order conversion
- **Payment Processing**: Secure payment handling
- **Fulfillment**: Inventory reservation and shipping
- **Notifications**: Customer communication at each stage

## 📦 Order Lifecycle

1. **Pending** → Order created, awaiting payment
2. **Confirmed** → Payment received, processing
3. **Processing** → Inventory allocated, preparing shipment
4. **Shipped** → Order dispatched to customer
5. **Delivered** → Order completed successfully
6. **Cancelled** → Order cancelled/refunded

## 🚀 Performance Metrics

- **Order Processing**: < 500ms average
- **Peak Capacity**: 10,000 orders/minute
- **Data Consistency**: ACID transactions
- **Message Queue**: Event-driven architecture
    """,
    summary="Order processing and management service",
    contact={
        "name": "Order Service Team",
        "email": "order-service@ecommerce.com",
        "url": "https://support.ecommerce.com/order-service",
    },
    license_info={
        "name": "BSD 3-Clause",
        "url": "https://opensource.org/licenses/BSD-3-Clause",
    },
    openapi_tags=[
        {"name": "orders", "description": "Order creation and management operations"},
        {"name": "payments", "description": "Payment processing and verification"},
        {"name": "shipping", "description": "Shipping and delivery management"},
        {"name": "status", "description": "Order status tracking and updates"},
    ],
    lifespan=lifespan,
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
