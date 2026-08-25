from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import httpx

from app.main import app

client = TestClient(app)

SAMPLE_TICKERS_JSON = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 1318605, "ticker": "TSLA", "title": "Tesla, Inc."},
    "2": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
}

SAMPLE_SUBMISSIONS_JSON = {
    "cik": "0000320193",
    "entityType": "operating",
    "sic": "3571",
    "name": "Apple Inc.",
    "tickers": ["AAPL"],
    "filings": {
        "recent": {
            "accessionNumber": [
                "0000320193-24-000106",
                "0000320193-24-000069",
                "0000320193-23-000106",
            ],
            "filingDate": ["2024-11-01", "2024-08-02", "2023-11-03"],
            "reportDate": ["2024-09-28", "2024-06-29", "2023-09-30"],
            "acceptanceDateTime": [
                "2024-11-01T18:00:00.000Z",
                "2024-08-02T18:00:00.000Z",
                "2023-11-03T18:00:00.000Z",
            ],
            "form": ["10-K", "10-Q", "10-K"],
            "primaryDocument": ["aapl-20240928.htm", "aapl-20240629.htm", "aapl-20230930.htm"],
            "primaryDocDescription": ["10-K", "10-Q", "10-K"],
        }
    },
}

SAMPLE_10K_HTML = """
<!DOCTYPE html>
<html>
<head><title>Apple Inc. 10-K</title></head>
<body>
    <div>
        <h2>Table of Contents</h2>
        <p>Item 1. Business ...... 5</p>
        <p>Item 1A. Risk Factors ...... 10</p>
        <p>Item 7. Management's Discussion and Analysis ...... 25</p>
    </div>
    <hr/>
    <div>
        <h1>Item 1. Business</h1>
        <p>Apple designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories, and sells a variety of related services. The Company’s fiscal year is the 52- or 53-week period that ends on the last Saturday of September.</p>
        <p>The Company is committed to bringing the best user experience to customers through its innovative hardware, software and services.</p>
    </div>
    <div>
        <h1>Item 1A. Risk Factors</h1>
        <p>The Company’s business, reputation, results of operations and financial condition can be adversely affected by many factors, including macroeconomic conditions, supply chain disruptions, geopolitical tensions, and rapid technological change.</p>
        <p>Global economic conditions could materially adversely affect the demand for the Company's products.</p>
    </div>
    <div>
        <h1>Item 1B. Unresolved Staff Comments</h1>
        <p>None.</p>
    </div>
    <div>
        <h1>Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations</h1>
        <p>Total net sales increased 2% or $8.1 billion during 2024 compared to 2023, driven by growth in Services and iPhone sales, partially offset by lower sales of Mac and iPad products.</p>
        <p>Gross margin percentage was 46.2% in 2024 compared to 44.1% in 2023.</p>
    </div>
    <div>
        <h1>Item 7A. Quantitative and Qualitative Disclosures About Market Risk</h1>
        <p>The Company is exposed to market risk from changes in foreign currency exchange rates and interest rates.</p>
    </div>
    <div>
        <h1>Item 8. Financial Statements and Supplementary Data</h1>
        <p>Consolidated statements of operations and balance sheets follow here.</p>
    </div>
    <div>
        <h1>Item 9. Controls and Procedures</h1>
        <p>Evaluation of disclosure controls and procedures.</p>
    </div>
</body>
</html>
"""

SAMPLE_10Q_HTML = """
<!DOCTYPE html>
<html>
<head><title>Apple Inc. 10-Q</title></head>
<body>
    <div>
        <h1>PART I — FINANCIAL INFORMATION</h1>
        <h2>Item 1. Financial Statements</h2>
        <p>Condensed consolidated financial statements of Apple Inc. for the quarterly period ended June 29, 2024.</p>
    </div>
    <div>
        <h2>Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations</h2>
        <p>Net sales were $85.8 billion in the third quarter of fiscal 2024, up 5% from the year-ago quarter. Services revenue reached an all-time record high of $24.2 billion.</p>
    </div>
    <div>
        <h2>Item 3. Quantitative and Qualitative Disclosures About Market Risk</h2>
        <p>There have been no material changes in our market risk disclosures.</p>
    </div>
    <div>
        <h1>PART II — OTHER INFORMATION</h1>
        <h2>Item 1A. Risk Factors</h2>
        <p>There have been no material changes from the risk factors previously disclosed in our Annual Report on Form 10-K.</p>
    </div>
    <div>
        <h2>Item 2. Unregistered Sales of Equity Securities</h2>
        <p>Share repurchase activity during the quarter.</p>
    </div>
</body>
</html>
"""


def mock_httpx_get_dispatcher(url: str, **kwargs):
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    if "company_tickers.json" in url:
        mock_resp.json.return_value = SAMPLE_TICKERS_JSON
    elif "submissions/CIK" in url:
        mock_resp.json.return_value = SAMPLE_SUBMISSIONS_JSON
    elif "aapl-20240928.htm" in url or "0000320193-24-000106" in url:
        mock_resp.text = SAMPLE_10K_HTML
    elif "aapl-20240629.htm" in url or "0000320193-24-000069" in url:
        mock_resp.text = SAMPLE_10Q_HTML
    else:
        mock_resp.status_code = 404
        mock_resp.text = "Not found"
    return mock_resp


@patch("httpx.Client.get", side_effect=mock_httpx_get_dispatcher)
def test_list_filings_all(mock_get):
    """Test retrieving list of all recent filings for a valid ticker."""
    response = client.get("/api/v1/sec/filings?ticker=AAPL&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["cik"] == "0000320193"
    assert data["company_name"] == "Apple Inc."
    assert data["total_count"] == 3
    assert len(data["filings"]) == 3
    assert data["filings"][0]["accession_number"] == "0000320193-24-000106"
    assert data["filings"][0]["form_type"] == "10-K"
    assert data["filings"][0]["filing_date"] == "2024-11-01"


@patch("httpx.Client.get", side_effect=mock_httpx_get_dispatcher)
def test_list_filings_filtered_by_form(mock_get):
    """Test retrieving filings filtered by form_type (e.g. 10-K only)."""
    response = client.get("/api/v1/sec/filings?ticker=AAPL&form_type=10-K&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    for f in data["filings"]:
        assert f["form_type"] == "10-K"


@patch("httpx.Client.get", side_effect=mock_httpx_get_dispatcher)
def test_list_filings_unknown_ticker(mock_get):
    """Test that an unknown ticker returns 404 Not Found."""
    response = client.get("/api/v1/sec/filings?ticker=INVALIDTICKERXYZ")
    assert response.status_code == 404
    assert "not found in SEC EDGAR directory" in response.json()["detail"]


@patch("httpx.Client.get", side_effect=mock_httpx_get_dispatcher)
def test_get_latest_10k_filing_parsed(mock_get):
    """Test fetching and parsing the latest 10-K filing for AAPL."""
    response = client.get("/api/v1/sec/filings/AAPL/latest?form_type=10-K")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["form_type"] == "10-K"
    assert data["accession_number"] == "0000320193-24-000106"
    assert "item_1" in data["sections"]
    assert "item_1a" in data["sections"]
    assert "item_7" in data["sections"]

    # Verify extracted content
    item_1 = data["sections"]["item_1"]
    assert item_1["title"] == "Item 1. Business"
    assert "Apple designs, manufactures and markets smartphones" in item_1["content"]

    item_1a = data["sections"]["item_1a"]
    assert item_1a["title"] == "Item 1A. Risk Factors"
    assert "supply chain disruptions" in item_1a["content"]

    item_7 = data["sections"]["item_7"]
    assert "Total net sales increased 2%" in item_7["content"]


@patch("httpx.Client.get", side_effect=mock_httpx_get_dispatcher)
def test_get_latest_10q_filing_parsed(mock_get):
    """Test fetching and parsing the latest 10-Q filing for AAPL."""
    response = client.get("/api/v1/sec/filings/AAPL/latest?form_type=10-Q")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["form_type"] == "10-Q"
    assert data["accession_number"] == "0000320193-24-000069"
    assert "part1_item2" in data["sections"]
    assert "part2_item1a" in data["sections"]

    mda = data["sections"]["part1_item2"]
    assert "Net sales were $85.8 billion" in mda["content"]


@patch("httpx.Client.get", side_effect=mock_httpx_get_dispatcher)
def test_get_filing_by_accession_success(mock_get):
    """Test fetching and parsing a specific filing by accession number."""
    response = client.get("/api/v1/sec/filings/AAPL/0000320193-24-000106?form_type=10-K")
    assert response.status_code == 200
    data = response.json()
    assert data["accession_number"] == "0000320193-24-000106"
    assert "item_1a" in data["sections"]


@patch("httpx.Client.get")
def test_sec_edgar_network_error(mock_get):
    """Test handling of SEC network or connection errors."""
    mock_get.side_effect = httpx.ConnectError("Connection refused by SEC EDGAR")
    response = client.get("/api/v1/sec/filings?ticker=AAPL")
    assert response.status_code == 502
    assert "Failed to connect to SEC EDGAR" in response.json()["detail"]


@patch("httpx.Client.get", side_effect=mock_httpx_get_dispatcher)
def test_get_latest_filing_not_found(mock_get):
    """Test 404 response when no filings match the requested form_type."""
    response = client.get("/api/v1/sec/filings/AAPL/latest?form_type=8-K")
    assert response.status_code == 404
    assert "No 8-K filings found" in response.json()["detail"]


def test_list_filings_invalid_query():
    """Test query parameter validation when ticker is empty."""
    response = client.get("/api/v1/sec/filings?ticker=")
    assert response.status_code == 422
