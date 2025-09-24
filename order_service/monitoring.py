from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from fastapi import Response
import logging

logger = logging.getLogger(__name__)

# Order-specific metrics
ORDER_REQUESTS = Counter(
    "order_requests_total",
    "Total order API requests",
    ["method", "endpoint", "status_code"],
)

ORDER_REQUEST_DURATION = Histogram(
    "order_request_duration_seconds",
    "Order request duration in seconds",
    ["method", "endpoint"],
)

ORDERS_CREATED = Counter("orders_created_total", "Total orders created")

ORDERS_COMPLETED = Counter(
    "orders_completed_total", "Total orders completed successfully"
)

ORDER_REVENUE = Gauge("order_revenue_total", "Total revenue from orders")

ORDER_STATUS = Gauge("orders_by_status", "Number of orders by status", ["status"])


def monitor_app(app, app_name: str):
    """
    Set up monitoring for Order Service
    """
    Instrumentator().instrument(app).expose(app)

    @app.middleware("http")
    async def monitor_order_requests(request, call_next):
        start_time = time.time()

        response = await call_next(request)
        process_time = time.time() - start_time

        ORDER_REQUESTS.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()

        ORDER_REQUEST_DURATION.labels(
            method=request.method, endpoint=request.url.path
        ).observe(process_time)

        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Service"] = app_name

        return response

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type="text/plain")

    @app.get("/metrics/business")
    async def business_metrics():
        return {
            "service": app_name,
            "metrics": {
                "orders_created": ORDERS_CREATED._value.get(),
                "orders_completed": ORDERS_COMPLETED._value.get(),
                "total_revenue": ORDER_REVENUE._value.get(),
                "total_requests": ORDER_REQUESTS._value.get(),
            },
        }

    logger.info(f"Order monitoring enabled for {app_name}")


# Business metric tracking
def track_order_creation():
    """Track new order creation"""
    ORDERS_CREATED.inc()


def track_order_completion():
    """Track order completion"""
    ORDERS_COMPLETED.inc()


def track_revenue(amount: float):
    """Track revenue from orders"""
    ORDER_REVENUE.inc(amount)


def track_order_status(status: str, count: int):
    """Track number of orders by status"""
    ORDER_STATUS.labels(status=status).set(count)
