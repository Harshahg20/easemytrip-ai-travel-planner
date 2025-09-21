import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.main import app
from app.core.database import get_db, Base
from app.models.trip import Trip

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_trip():
    """Test creating a new trip"""
    trip_data = {
        "destination": "Rajasthan",
        "start_date": "2024-01-15T00:00:00",
        "end_date": "2024-01-20T00:00:00",
        "total_budget": 50000,
        "travelers": 2,
        "themes": ["cultural", "heritage"]
    }
    
    response = client.post("/api/v1/trips/", json=trip_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["destination"] == "Rajasthan"
    assert data["total_budget"] == 50000
    assert data["travelers"] == 2
    assert data["status"] == "draft"

def test_get_trip():
    """Test getting a trip by ID"""
    # First create a trip
    trip_data = {
        "destination": "Kerala",
        "start_date": "2024-02-01T00:00:00",
        "end_date": "2024-02-05T00:00:00",
        "total_budget": 30000,
        "travelers": 1
    }
    
    create_response = client.post("/api/v1/trips/", json=trip_data)
    trip_id = create_response.json()["id"]
    
    # Now get the trip
    response = client.get(f"/api/v1/trips/{trip_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["destination"] == "Kerala"
    assert data["id"] == trip_id

def test_list_trips():
    """Test listing all trips"""
    response = client.get("/api/v1/trips/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)

def test_update_trip():
    """Test updating a trip"""
    # First create a trip
    trip_data = {
        "destination": "Goa",
        "start_date": "2024-03-01T00:00:00",
        "end_date": "2024-03-05T00:00:00",
        "total_budget": 40000,
        "travelers": 2
    }
    
    create_response = client.post("/api/v1/trips/", json=trip_data)
    trip_id = create_response.json()["id"]
    
    # Update the trip
    update_data = {
        "total_budget": 45000,
        "status": "planned"
    }
    
    response = client.put(f"/api/v1/trips/{trip_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_budget"] == 45000
    assert data["status"] == "planned"

def test_delete_trip():
    """Test deleting a trip"""
    # First create a trip
    trip_data = {
        "destination": "Himachal Pradesh",
        "start_date": "2024-04-01T00:00:00",
        "end_date": "2024-04-05T00:00:00",
        "total_budget": 35000,
        "travelers": 2
    }
    
    create_response = client.post("/api/v1/trips/", json=trip_data)
    trip_id = create_response.json()["id"]
    
    # Delete the trip
    response = client.delete(f"/api/v1/trips/{trip_id}")
    assert response.status_code == 200
    
    # Try to get the deleted trip
    get_response = client.get(f"/api/v1/trips/{trip_id}")
    assert get_response.status_code == 404

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
