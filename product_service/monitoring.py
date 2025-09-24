from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from fastapi import Response
import logging

logger = logging.getLogger(__name__)

# Product-specific metrics
PRODUCT_REQUESTS = Counter(
    "product_requests_total",
    "Total product API requests",
    ["method", "endpoint", "status_code"],
)

PRODUCT_REQUEST_DURATION = Histogram(
    "product_request_duration_seconds",
    "Product request duration in seconds",
    ["method", "endpoint"],
)

PRODUCT_CREATIONS = Counter("products_created_total", "Total products created")

PRODUCT_UPDATES = Counter("products_updated_total", "Total products updated")

PRODUCT_INVENTORY = Gauge(
    "product_inventory_total", "Total products in inventory", ["category"]
)


def monitor_app(app, app_name: str):
    """
    Set up monitoring for Product Service
    """
    # Instrument with Prometheus
    Instrumentator().instrument(app).expose(app)

    # Custom middleware for product-specific metrics
    @app.middleware("http")
    async def monitor_product_requests(request, call_next):
        start_time = time.time()

        response = await call_next(request)
        process_time = time.time() - start_time

        # Track product-specific metrics
        PRODUCT_REQUESTS.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()

        PRODUCT_REQUEST_DURATION.labels(
            method=request.method, endpoint=request.url.path
        ).observe(process_time)

        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Service"] = app_name

        return response

    # Metrics endpoint
    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type="text/plain")

    # Business metrics endpoint
    @app.get("/metrics/business")
    async def business_metrics():
        return {
            "service": app_name,
            "metrics": {
                "products_created": PRODUCT_CREATIONS._value.get(),
                "products_updated": PRODUCT_UPDATES._value.get(),
                "total_requests": PRODUCT_REQUESTS._value.get(),
            },
        }

    logger.info(f"Product monitoring enabled for {app_name}")


# Business metric tracking functions
def track_product_creation():
    """Track when a new product is created"""
    PRODUCT_CREATIONS.inc()


def track_product_update():
    """Track when a product is updated"""
    PRODUCT_UPDATES.inc()


def track_inventory_change(category: str, quantity: int):
    """Track inventory changes by category"""
    PRODUCT_INVENTORY.labels(category=category).set(quantity)
