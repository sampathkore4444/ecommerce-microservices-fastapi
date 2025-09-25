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
    description="Order management service",
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
