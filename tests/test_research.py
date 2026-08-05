import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from huggingface_hub.errors import HfHubHTTPError

from app.main import app

client = TestClient(app)

SAMPLE_HF_RESPONSE_CONTENT = json.dumps({
    "company_name": "Apple Inc.",
    "summary": "Apple generates revenue primarily through consumer hardware sales and expanding digital services.",
    "primary_currency": "USD",
    "revenue_streams": [
        {
            "name": "iPhone",
            "description": "Sales of flagship smartphone devices worldwide.",
            "revenue_type": "Product Sales",
            "estimated_percentage": 52.0,
        },
        {
            "name": "Services",
            "description": "App Store, Apple Music, iCloud, and ApplePay subscriptions.",
            "revenue_type": "Subscription",
            "estimated_percentage": 22.0,
        },
    ],
})


def make_mock_chat_completion(content: str):
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    return mock_completion


@patch("app.services.revenue_researcher.InferenceClient")
def test_analyze_revenue_streams_success(mock_inference_client):
    """Test successful revenue stream analysis endpoint response with mocked HF API."""
    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.return_value = make_mock_chat_completion(
        f"```json\n{SAMPLE_HF_RESPONSE_CONTENT}\n```"
    )
    mock_inference_client.return_value = mock_client_instance

    payload = {"company_name": "Apple Inc."}
    response = client.post("/api/v1/research/revenue-streams", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Apple Inc."
    assert "Apple generates revenue" in data["summary"]
    assert data["primary_currency"] == "USD"
    assert len(data["revenue_streams"]) == 2
    assert data["revenue_streams"][0]["name"] == "iPhone"
    assert data["revenue_streams"][0]["estimated_percentage"] == 52.0
    assert data["model_used"] == "meta-llama/Llama-3.1-8B-Instruct"


@patch("app.services.revenue_researcher.InferenceClient")
def test_analyze_revenue_streams_custom_model(mock_inference_client):
    """Test revenue stream analysis endpoint using a custom model_id override."""
    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.return_value = make_mock_chat_completion(
        SAMPLE_HF_RESPONSE_CONTENT
    )
    mock_inference_client.return_value = mock_client_instance

    custom_model = "Qwen/Qwen2.5-72B-Instruct"
    payload = {"company_name": "Apple Inc.", "model_id": custom_model}
    response = client.post("/api/v1/research/revenue-streams", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["model_used"] == custom_model


@patch("app.services.revenue_researcher.InferenceClient")
def test_analyze_revenue_streams_invalid_json(mock_inference_client):
    """Test that invalid non-JSON LLM responses trigger a 502 Bad Gateway response."""
    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.return_value = make_mock_chat_completion(
        "Sorry, I cannot produce JSON right now."
    )
    mock_inference_client.return_value = mock_client_instance

    payload = {"company_name": "Tesla Inc."}
    response = client.post("/api/v1/research/revenue-streams", json=payload)

    assert response.status_code == 502
    assert "could not be parsed as valid JSON" in response.json()["detail"]


@patch("app.services.revenue_researcher.InferenceClient")
def test_analyze_revenue_streams_hf_error(mock_inference_client):
    """Test that Hugging Face API errors trigger a 502 Bad Gateway response."""
    mock_client_instance = MagicMock()

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized access - invalid token"

    mock_client_instance.chat.completions.create.side_effect = HfHubHTTPError(
        "Unauthorized access", response=mock_response
    )
    mock_inference_client.return_value = mock_client_instance

    payload = {"company_name": "Microsoft"}
    response = client.post("/api/v1/research/revenue-streams", json=payload)

    assert response.status_code == 502
    assert "Hugging Face API request failed" in response.json()["detail"]


def test_analyze_revenue_streams_invalid_payload():
    """Test request body validation failure when company_name is missing or empty."""
    payload = {"company_name": ""}
    response = client.post("/api/v1/research/revenue-streams", json=payload)
    assert response.status_code == 422
