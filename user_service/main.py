from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from database import Base, engine
from routers import auth, users

from monitoring import monitor_app

from contextlib import asynccontextmanager
import asyncio
from .event_handlers import message_queue, handle_order_events, MessageType


# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to message queue
    await message_queue.connect()

    # Start consuming order events for user analytics
    order_task = asyncio.create_task(
        message_queue.consume_messages(MessageType.ORDER_CREATED, handle_order_events)
    )

    yield

    # Shutdown: Close connections
    order_task.cancel()
    await message_queue.close()


app = FastAPI(
    title="User Service",
    version="1.0.0",
    description="User management and authentication service",
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
app.include_router(auth.router)
app.include_router(users.router)

# 🔍 THIS IS THE MONITORING SETUP
monitor_app(app, "user_service")
# What it does:
# 1. Sets up Prometheus metrics collection
# 2. Adds request/response monitoring middleware
# 3. Creates /metrics endpoint for monitoring systems
# 4. Enables performance tracking


# ✅ HEALTH CHECK ENDPOINT
@app.get("/health")
async def health_check():
    """
    Simple health check for load balancers and monitoring
    This is a BASIC health check - just returns status
    """
    return {"status": "healthy", "service": "user_service"}


# ✅ ENHANCED HEALTH CHECK (optional)
@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check including database connectivity
    and other dependencies
    """
    try:
        # Check database connection
        from database import SessionLocal

        db = SessionLocal()
        db.execute("SELECT 1")  # Simple database check
        db.close()

        return {
            "status": "healthy",
            "service": "user_service",
            "database": "connected",
            "timestamp": "2024-01-01T12:00:00Z",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "user_service",
            "database": "disconnected",
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
