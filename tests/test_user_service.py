import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app, get_db
from models import Base, User
from shared.schemas import UserCreate

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
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

client = TestClient(app)


@pytest.fixture
def test_user():
    return UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password="testpassword",
    )


def test_create_user(test_user):
    response = client.post("/users/", json=test_user.dict())
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert "password" not in data


def test_login_success(test_user):
    # First create user
    client.post("/users/", json=test_user.dict())

    # Then login
    response = client.post(
        "/token", data={"username": test_user.username, "password": test_user.password}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure():
    response = client.post(
        "/token", data={"username": "nonexistent", "password": "wrongpassword"}
    )
    assert response.status_code == 401
