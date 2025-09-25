import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from order_service.main import app
from order_service.database import get_db
from order_service.models import Base, Order

# Test database
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture
def test_order(db_session):
    order = Order(
        id="order-123",
        user_id="user-123",
        items=[{"product_id": "prod-123", "quantity": 2, "price": 29.99}],
        total_amount=59.98,
        status="pending",
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order
