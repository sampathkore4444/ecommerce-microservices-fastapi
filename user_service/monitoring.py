from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, generate_latest
import time
from fastapi import Response
import logging

logger = logging.getLogger(__name__)

# Custom metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total Request Count",
    ["app_name", "method", "endpoint", "http_status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_USERS = Counter("active_users_total", "Total number of active users")


def monitor_app(app, app_name: str):
    """
    Set up monitoring and metrics for the FastAPI application
    """

    # 1. Instrument the app with Prometheus metrics
    Instrumentator().instrument(app).expose(app)

    # 2. Add custom middleware for request tracking
    @app.middleware("http")
    async def monitor_requests(request, call_next):
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Track metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method, endpoint=request.url.path
        ).observe(process_time)

        # Add custom header with processing time
        response.headers["X-Process-Time"] = str(process_time)

        return response

    # 3. Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type="text/plain")

    # 4. Add custom metrics endpoint
    @app.get("/metrics/custom")
    async def custom_metrics():
        metrics_data = {
            "service": app_name,
            "timestamp": time.time(),
            "custom_metrics": {
                "total_requests": REQUEST_COUNT._value.get(),
                "active_users": ACTIVE_USERS._value.get(),
            },
        }
        return metrics_data

    logger.info(f"Monitoring enabled for {app_name}")


# Example of tracking business metrics
def track_user_registration():
    """Track when a new user registers"""
    ACTIVE_USERS.inc()
    logger.info("New user registration tracked")
