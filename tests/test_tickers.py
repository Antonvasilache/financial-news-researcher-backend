import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.tickers import ticker_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_ticker_db():
    """
    Fixture that runs automatically before every test to reset
    the in-memory state so tests remain isolated and predictable.
    """
    ticker_db.clear()
    ticker_db[1] = {
        "id": 1,
        "symbol": "AMD",
        "company_name": "Advanced Micro Devices, Inc.",
        "is_active": True,
        "created_at": "2026-08-02T10:00:00Z"
    }
    
    import app.routers.tickers as tickers_module
    tickers_module.id_counter = 2


def test_root_endpoint():
    """Verify backend health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Financial News Researcher API is running"}


def test_get_all_tickers():
    """Test retrieving all tracked tickers."""
    response = client.get("/tickers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AMD"


def test_get_single_ticker_success():
    """Test retrieving an existing ticker by ID."""
    response = client.get("/tickers/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["symbol"] == "AMD"


def test_get_single_ticker_not_found():
    """Test retrieving a non-existent ticker returns 404."""
    response = client.get("/tickers/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Ticker with ID 999 not found"


def test_create_ticker_success():
    """Test adding a valid new ticker."""
    payload = {
        "symbol": "nvda",
        "company_name": "NVIDIA Corporation"
    }
    response = client.post("/tickers/", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["symbol"] == "NVDA"
    assert data["id"] == 2
    assert "created_at" in data


def test_create_duplicate_ticker_fails():
    """Test that attempting to add an existing ticker returns 400."""
    payload = {
        "symbol": "AMD",
        "company_name": "Advanced Micro Devices, Inc."
    }
    response = client.post("/tickers/", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_delete_ticker_success():
    """Test deleting an existing ticker."""
    response = client.delete("/tickers/1")
    assert response.status_code == 204
    
    get_response = client.get("/tickers/1")
    assert get_response.status_code == 404


def test_delete_ticker_not_found():
    """Test deleting a non-existent ticker returns 404."""
    response = client.delete("/tickers/999")
    assert response.status_code == 404