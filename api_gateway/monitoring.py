from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from fastapi import Response
import logging
import httpx

logger = logging.getLogger(__name__)

# API Gateway specific metrics
GATEWAY_REQUESTS = Counter(
    "gateway_requests_total",
    "Total gateway requests",
    ["method", "endpoint", "status_code", "service"],
)

GATEWAY_REQUEST_DURATION = Histogram(
    "gateway_request_duration_seconds",
    "Gateway request duration including downstream services",
    ["method", "endpoint", "service"],
)

DOWNSTREAM_REQUESTS = Counter(
    "downstream_requests_total",
    "Requests to downstream services",
    ["service", "status_code"],
)

DOWNSTREAM_ERRORS = Counter(
    "downstream_errors_total", "Errors from downstream services", ["service"]
)

GATEWAY_ACTIVE_REQUESTS = Gauge(
    "gateway_active_requests", "Currently active requests in gateway"
)


def monitor_app(app, app_name: str):
    """
    Set up monitoring for API Gateway
    """
    Instrumentator().instrument(app).expose(app)

    @app.middleware("http")
    async def monitor_gateway_requests(request, call_next):
        GATEWAY_ACTIVE_REQUESTS.inc()
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Determine which service was called
            service = "gateway"  # Default
            if request.url.path.startswith("/users"):
                service = "user_service"
            elif request.url.path.startswith("/products"):
                service = "product_service"
            elif request.url.path.startswith("/orders"):
                service = "order_service"

            GATEWAY_REQUESTS.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                service=service,
            ).inc()

            GATEWAY_REQUEST_DURATION.labels(
                method=request.method, endpoint=request.url.path, service=service
            ).observe(process_time)

            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Gateway-Service"] = service

            return response
        finally:
            GATEWAY_ACTIVE_REQUESTS.dec()

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type="text/plain")

    @app.get("/metrics/gateway")
    async def gateway_metrics():
        return {
            "service": app_name,
            "metrics": {
                "total_requests": GATEWAY_REQUESTS._value.get(),
                "active_requests": GATEWAY_ACTIVE_REQUESTS._value.get(),
                "downstream_errors": DOWNSTREAM_ERRORS._value.get(),
            },
            "timestamp": time.time(),
        }

    logger.info(f"Gateway monitoring enabled for {app_name}")


# Downstream service tracking
def track_downstream_request(service: str, status_code: int):
    """Track requests to downstream services"""
    DOWNSTREAM_REQUESTS.labels(service=service, status_code=status_code).inc()

    if status_code >= 400:
        DOWNSTREAM_ERRORS.labels(service=service).inc()


def track_downstream_error(service: str):
    """Track errors from downstream services"""
    DOWNSTREAM_ERRORS.labels(service=service).inc()
