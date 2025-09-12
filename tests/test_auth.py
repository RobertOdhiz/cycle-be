import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

client = TestClient(app)


@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    with Session(engine) as session:
        yield session


def test_signup():
    """Test user signup"""
    response = client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "name": "Test User",
        "phone": "+254700000000",
        "school": "Test University",
        "year": "2"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "user_id" in data["data"]


def test_login():
    """Test user login"""
    # First signup
    client.post("/auth/signup", json={
        "email": "login@example.com",
        "password": "TestPass123!",
        "name": "Login User"
    })
    
    # Then login
    response = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "TestPass123!"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_invalid_login():
    """Test invalid login credentials"""
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "WrongPassword"
    })
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Incorrect email or password"
