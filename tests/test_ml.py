from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.financials import (
    CompanyFinancialsResponse,
    FinancialRatios,
    FinancialStatementMetrics,
    PeriodFinancials,
)
from app.schemas.ml import (
    AnomalySeverity,
    FinancialTrendCategory,
)
from app.services.ml_analyzer import FinancialMLAnalyzerService

client = TestClient(app)

SAMPLE_TICKERS_JSON = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
}

SAMPLE_COMPANY_FACTS_JSON = {
    "cik": 320193,
    "entityName": "Apple Inc.",
    "facts": {
        "us-gaap": {
            "Revenues": {
                "units": {
                    "USD": [
                        {
                            "start": "2023-10-01",
                            "end": "2023-12-30",
                            "val": 119575000000.0,
                            "fy": 2024,
                            "fp": "Q1",
                            "form": "10-Q",
                            "filed": "2024-02-02",
                        },
                        {
                            "start": "2024-03-31",
                            "end": "2024-06-29",
                            "val": 85777000000.0,
                            "fy": 2024,
                            "fp": "Q3",
                            "form": "10-Q",
                            "filed": "2024-08-02",
                        },
                    ]
                }
            },
            "OperatingIncomeLoss": {
                "units": {
                    "USD": [
                        {
                            "start": "2023-10-01",
                            "end": "2023-12-30",
                            "val": 40373000000.0,
                            "fy": 2024,
                            "fp": "Q1",
                            "form": "10-Q",
                            "filed": "2024-02-02",
                        },
                        {
                            "start": "2024-03-31",
                            "end": "2024-06-29",
                            "val": 25352000000.0,
                            "fy": 2024,
                            "fp": "Q3",
                            "form": "10-Q",
                            "filed": "2024-08-02",
                        },
                    ]
                }
            },
            "NetIncomeLoss": {
                "units": {
                    "USD": [
                        {
                            "start": "2023-10-01",
                            "end": "2023-12-30",
                            "val": 33916000000.0,
                            "fy": 2024,
                            "fp": "Q1",
                            "form": "10-Q",
                            "filed": "2024-02-02",
                        },
                        {
                            "start": "2024-03-31",
                            "end": "2024-06-29",
                            "val": 21448000000.0,
                            "fy": 2024,
                            "fp": "Q3",
                            "form": "10-Q",
                            "filed": "2024-08-02",
                        },
                    ]
                }
            },
            "AssetsCurrent": {
                "units": {
                    "USD": [
                        {
                            "end": "2024-06-29",
                            "val": 133500000000.0,
                            "fy": 2024,
                            "fp": "Q3",
                            "form": "10-Q",
                            "filed": "2024-08-02",
                        }
                    ]
                }
            },
            "LiabilitiesCurrent": {
                "units": {
                    "USD": [
                        {
                            "end": "2024-06-29",
                            "val": 125000000000.0,
                            "fy": 2024,
                            "fp": "Q3",
                            "form": "10-Q",
                            "filed": "2024-08-02",
                        }
                    ]
                }
            },
            "Assets": {
                "units": {
                    "USD": [
                        {
                            "end": "2024-06-29",
                            "val": 364980000000.0,
                            "fy": 2024,
                            "fp": "Q3",
                            "form": "10-Q",
                            "filed": "2024-08-02",
                        }
                    ]
                }
            },
            "StockholdersEquity": {
                "units": {
                    "USD": [
                        {
                            "end": "2024-06-29",
                            "val": 66700000000.0,
                            "fy": 2024,
                            "fp": "Q3",
                            "form": "10-Q",
                            "filed": "2024-08-02",
                        }
                    ]
                }
            },
        }
    },
}


def build_mock_period(
    period_label: str,
    fiscal_year: int,
    fiscal_period: str,
    revenue: float,
    operating_income: float,
    gross_profit: float,
    net_income: float,
    current_assets: float,
    current_liabilities: float,
    total_assets: float,
    stockholders_equity: float,
    total_debt: float,
    operating_cash_flow: float,
    revenue_growth_yoy: float | None = None,
    cost_of_revenue: float | None = None,
    total_liabilities: float | None = None,
    cash_and_equivalents: float | None = None,
    eps: float | None = None,
    debt_to_assets: float | None = None,
    return_on_equity: float | None = None,
    return_on_assets: float | None = None,
    net_income_growth_yoy: float | None = None,
    filed_date: str | None = None,
) -> PeriodFinancials:
    gross_margin = gross_profit / revenue if revenue else None
    operating_margin = operating_income / revenue if revenue else None
    net_margin = net_income / revenue if revenue else None
    current_ratio = (
        current_assets / current_liabilities if current_liabilities else None
    )
    debt_to_equity = (
        total_debt / stockholders_equity
        if (stockholders_equity and stockholders_equity > 0)
        else None
    )

    metrics = FinancialStatementMetrics(
        revenue=revenue,
        cost_of_revenue=cost_of_revenue,
        gross_profit=gross_profit,
        operating_income=operating_income,
        net_income=net_income,
        operating_cash_flow=operating_cash_flow,
        current_assets=current_assets,
        total_assets=total_assets,
        current_liabilities=current_liabilities,
        total_liabilities=total_liabilities,
        stockholders_equity=stockholders_equity,
        cash_and_equivalents=cash_and_equivalents,
        total_debt=total_debt,
        eps=eps,
    )
    ratios = FinancialRatios(
        gross_margin=gross_margin,
        operating_margin=operating_margin,
        net_margin=net_margin,
        current_ratio=current_ratio,
        debt_to_equity=debt_to_equity,
        debt_to_assets=debt_to_assets,
        return_on_equity=return_on_equity,
        return_on_assets=return_on_assets,
        revenue_growth_yoy=revenue_growth_yoy,
        net_income_growth_yoy=net_income_growth_yoy,
    )
    return PeriodFinancials(
        period=period_label,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        end_date="2024-06-30",
        filed_date=filed_date,
        form="10-Q",
        metrics=metrics,
        ratios=ratios,
    )


# --- Service Unit Tests ---


def test_feature_vector_extraction_and_safe_defaults():
    service = FinancialMLAnalyzerService()
    period_one = build_mock_period(
        period_label="2024-Q1",
        fiscal_year=2024,
        fiscal_period="Q1",
        revenue=100000.0,
        operating_income=20000.0,
        gross_profit=50000.0,
        net_income=15000.0,
        current_assets=80000.0,
        current_liabilities=40000.0,
        total_assets=200000.0,
        stockholders_equity=100000.0,
        total_debt=30000.0,
        operating_cash_flow=22000.0,
    )
    period_two = build_mock_period(
        period_label="2024-Q2",
        fiscal_year=2024,
        fiscal_period="Q2",
        revenue=120000.0,
        operating_income=26000.0,
        gross_profit=62000.0,
        net_income=19000.0,
        current_assets=95000.0,
        current_liabilities=45000.0,
        total_assets=220000.0,
        stockholders_equity=110000.0,
        total_debt=33000.0,
        operating_cash_flow=27000.0,
        revenue_growth_yoy=0.20,
    )

    features = service.extract_feature_vector(
        current_period=period_two, previous_period=period_one
    )
    assert "revenue_growth_yoy" in features
    assert features["revenue_growth_yoy"] == 0.20
    assert pytest.approx(features["operating_margin"], abs=0.01) == 0.217
    assert pytest.approx(features["operating_margin_delta"], abs=0.005) == 0.017
    assert pytest.approx(features["current_ratio"], abs=0.01) == 2.11


def test_accelerating_growth_profile_classification():
    service = FinancialMLAnalyzerService()
    period_prior = build_mock_period(
        period_label="2024-Q1",
        fiscal_year=2024,
        fiscal_period="Q1",
        revenue=100000.0,
        operating_income=22000.0,
        gross_profit=54000.0,
        net_income=16000.0,
        current_assets=80000.0,
        current_liabilities=40000.0,
        total_assets=200000.0,
        stockholders_equity=120000.0,
        total_debt=30000.0,
        operating_cash_flow=25000.0,
    )
    period_current = build_mock_period(
        period_label="2024-Q2",
        fiscal_year=2024,
        fiscal_period="Q2",
        revenue=135000.0,
        operating_income=35000.0,
        gross_profit=77000.0,
        net_income=26000.0,
        current_assets=120000.0,
        current_liabilities=50000.0,
        total_assets=260000.0,
        stockholders_equity=150000.0,
        total_debt=32000.0,
        operating_cash_flow=38000.0,
        revenue_growth_yoy=0.35,
    )

    company_financials = CompanyFinancialsResponse(
        ticker="GROWTH",
        cik="0000111111",
        company_name="High Growth Tech Corp",
        quarterly_reports=[period_current, period_prior],
    )

    result = service.analyze_financials(company_financials, period_type="quarterly")
    assert result.trend_classification.category == FinancialTrendCategory.ACCELERATING_GROWTH
    assert result.trend_classification.confidence >= 0.70
    assert result.anomaly_detection.status == AnomalySeverity.NORMAL
    assert result.anomaly_detection.is_anomaly is False
    assert len(result.trend_classification.key_drivers) > 0


def test_stable_compounder_profile_classification():
    service = FinancialMLAnalyzerService()
    period_prior = build_mock_period(
        period_label="2024-Q1",
        fiscal_year=2024,
        fiscal_period="Q1",
        revenue=100000.0,
        operating_income=16000.0,
        gross_profit=42000.0,
        net_income=11000.0,
        current_assets=70000.0,
        current_liabilities=40000.0,
        total_assets=180000.0,
        stockholders_equity=90000.0,
        total_debt=75000.0,
        operating_cash_flow=15000.0,
    )
    period_current = build_mock_period(
        period_label="2024-Q2",
        fiscal_year=2024,
        fiscal_period="Q2",
        revenue=107000.0,
        operating_income=17200.0,
        gross_profit=45000.0,
        net_income=11800.0,
        current_assets=74000.0,
        current_liabilities=42000.0,
        total_assets=190000.0,
        stockholders_equity=95000.0,
        total_debt=78000.0,
        operating_cash_flow=16500.0,
        revenue_growth_yoy=0.07,
    )

    company_financials = CompanyFinancialsResponse(
        ticker="COMPOUND",
        cik="0000222222",
        company_name="Compounder Global Inc",
        quarterly_reports=[period_current, period_prior],
    )

    result = service.analyze_financials(company_financials, period_type="quarterly")
    assert result.trend_classification.category == FinancialTrendCategory.STABLE_COMPOUNDER
    assert result.anomaly_detection.status == AnomalySeverity.NORMAL
    assert result.anomaly_detection.is_anomaly is False


def test_margin_compression_profile_and_anomaly():
    service = FinancialMLAnalyzerService()
    period_prior = build_mock_period(
        period_label="2024-Q1",
        fiscal_year=2024,
        fiscal_period="Q1",
        revenue=100000.0,
        operating_income=14000.0,
        gross_profit=35000.0,
        net_income=9000.0,
        current_assets=60000.0,
        current_liabilities=45000.0,
        total_assets=180000.0,
        stockholders_equity=70000.0,
        total_debt=80000.0,
        operating_cash_flow=12000.0,
    )
    period_current = build_mock_period(
        period_label="2024-Q2",
        fiscal_year=2024,
        fiscal_period="Q2",
        revenue=108000.0,
        operating_income=6500.0,  # margin drops from 14% to 6.0% (drop of 800 bps)
        gross_profit=27000.0,
        net_income=3000.0,
        current_assets=58000.0,
        current_liabilities=46000.0,
        total_assets=185000.0,
        stockholders_equity=71000.0,
        total_debt=95000.0,  # debt up 18.7%
        operating_cash_flow=4000.0,
        revenue_growth_yoy=0.08,
    )

    company_financials = CompanyFinancialsResponse(
        ticker="SQUEEZE",
        cik="0000333333",
        company_name="Margin Squeeze Brands",
        quarterly_reports=[period_current, period_prior],
    )

    result = service.analyze_financials(company_financials, period_type="quarterly")
    assert result.trend_classification.category == FinancialTrendCategory.MARGIN_COMPRESSION
    assert result.anomaly_detection.is_anomaly is True
    assert any(
        divergence.metric_name == "operating_margin_delta"
        for divergence in result.anomaly_detection.detected_divergences
    )


def test_high_financial_stress_profile():
    service = FinancialMLAnalyzerService()
    period_prior = build_mock_period(
        period_label="2024-Q1",
        fiscal_year=2024,
        fiscal_period="Q1",
        revenue=100000.0,
        operating_income=-2000.0,
        gross_profit=18000.0,
        net_income=-5000.0,
        current_assets=35000.0,
        current_liabilities=50000.0,
        total_assets=150000.0,
        stockholders_equity=25000.0,
        total_debt=100000.0,
        operating_cash_flow=-3000.0,
    )
    period_current = build_mock_period(
        period_label="2024-Q2",
        fiscal_year=2024,
        fiscal_period="Q2",
        revenue=85000.0,
        operating_income=-12000.0,
        gross_profit=10000.0,
        net_income=-15000.0,
        current_assets=28000.0,
        current_liabilities=55000.0,  # current ratio = 0.51
        total_assets=140000.0,
        stockholders_equity=12000.0,
        total_debt=120000.0,  # debt/equity = 10.0
        operating_cash_flow=-8000.0,
        revenue_growth_yoy=-0.15,
    )

    company_financials = CompanyFinancialsResponse(
        ticker="STRESS",
        cik="0000444444",
        company_name="Distressed Solvency Ltd",
        quarterly_reports=[period_current, period_prior],
    )

    result = service.analyze_financials(company_financials, period_type="quarterly")
    assert result.trend_classification.category == FinancialTrendCategory.HIGH_FINANCIAL_STRESS
    assert result.anomaly_detection.is_anomaly is True
    assert any(
        divergence.metric_name == "current_ratio_liquidity"
        for divergence in result.anomaly_detection.detected_divergences
    )


def test_debt_escalation_divergence_flagged():
    service = FinancialMLAnalyzerService()
    period_prior = build_mock_period(
        period_label="2024-Q1",
        fiscal_year=2024,
        fiscal_period="Q1",
        revenue=100000.0,
        operating_income=15000.0,
        gross_profit=40000.0,
        net_income=10000.0,
        current_assets=50000.0,
        current_liabilities=35000.0,
        total_assets=150000.0,
        stockholders_equity=60000.0,
        total_debt=40000.0,
        operating_cash_flow=12000.0,
    )
    period_current = build_mock_period(
        period_label="2024-Q2",
        fiscal_year=2024,
        fiscal_period="Q2",
        revenue=102000.0,  # +2% revenue growth
        operating_income=15000.0,
        gross_profit=40000.0,
        net_income=10000.0,
        current_assets=52000.0,
        current_liabilities=36000.0,
        total_assets=170000.0,
        stockholders_equity=60000.0,
        total_debt=65000.0,  # +62.5% debt growth! Divergence > 60%
        operating_cash_flow=12000.0,
        revenue_growth_yoy=0.02,
    )

    company_financials = CompanyFinancialsResponse(
        ticker="DEBTPACK",
        cik="0000555555",
        company_name="Leverage Surge Inc",
        quarterly_reports=[period_current, period_prior],
    )

    result = service.analyze_financials(company_financials, period_type="quarterly")
    assert result.anomaly_detection.is_anomaly is True
    debt_divergences = [
        item
        for item in result.anomaly_detection.detected_divergences
        if item.metric_name == "revenue_to_debt_divergence"
    ]
    assert len(debt_divergences) == 1
    assert debt_divergences[0].severity == "SEVERE_ANOMALY"


def test_negative_operating_cash_flow_divergence_flagged():
    service = FinancialMLAnalyzerService()
    period_current = build_mock_period(
        period_label="2024-Q2",
        fiscal_year=2024,
        fiscal_period="Q2",
        revenue=150000.0,
        operating_income=25000.0,
        gross_profit=60000.0,
        net_income=20000.0,  # positive net income
        current_assets=80000.0,
        current_liabilities=50000.0,
        total_assets=200000.0,
        stockholders_equity=100000.0,
        total_debt=40000.0,
        operating_cash_flow=-15000.0,  # sharply negative cash flow
        revenue_growth_yoy=0.08,
    )

    company_financials = CompanyFinancialsResponse(
        ticker="CASHBURN",
        cik="0000666666",
        company_name="Cash Burn Metrics Inc",
        quarterly_reports=[period_current],
    )

    result = service.analyze_financials(company_financials, period_type="quarterly")
    assert result.anomaly_detection.is_anomaly is True
    cf_divergences = [
        item
        for item in result.anomaly_detection.detected_divergences
        if item.metric_name == "operating_cash_flow_divergence"
    ]
    assert len(cf_divergences) == 1
    assert cf_divergences[0].severity == "SEVERE_ANOMALY"


def test_negative_stockholders_equity_divergence_flagged():
    service = FinancialMLAnalyzerService()
    period_current = build_mock_period(
        period_label="2024-Q2",
        fiscal_year=2024,
        fiscal_period="Q2",
        revenue=100000.0,
        operating_income=12000.0,
        gross_profit=40000.0,
        net_income=8000.0,
        current_assets=60000.0,
        current_liabilities=50000.0,
        total_assets=150000.0,
        stockholders_equity=-15000.0,  # negative stockholders' equity
        total_debt=80000.0,
        operating_cash_flow=10000.0,
    )

    company_financials = CompanyFinancialsResponse(
        ticker="NEGEQUITY",
        cik="0000777777",
        company_name="Negative Equity Corp",
        quarterly_reports=[period_current],
    )

    result = service.analyze_financials(company_financials, period_type="quarterly")
    equity_divergences = [
        item
        for item in result.anomaly_detection.detected_divergences
        if item.metric_name == "negative_stockholders_equity"
    ]
    assert len(equity_divergences) == 1
    assert equity_divergences[0].severity == "CAUTION"


def test_empty_reports_edge_case():
    service = FinancialMLAnalyzerService()
    company_financials = CompanyFinancialsResponse(
        ticker="EMPTY",
        cik="0000888888",
        company_name="Zero Reports Corp",
        quarterly_reports=[],
        annual_reports=[],
    )

    result = service.analyze_financials(company_financials)
    assert result.analyzed_period == "N/A"
    assert result.periods_analyzed_count == 0
    assert result.anomaly_detection.status == AnomalySeverity.NORMAL
    assert result.trend_classification.category == FinancialTrendCategory.STABLE_COMPOUNDER
    assert result.historical_sequence == []


# --- HTTP Endpoint Integration Tests ---


@patch("httpx.Client.get")
def test_analyze_company_endpoint_success(mock_get):
    tickers_response = MagicMock()
    tickers_response.status_code = 200
    tickers_response.json.return_value = SAMPLE_TICKERS_JSON

    facts_response = MagicMock()
    facts_response.status_code = 200
    facts_response.json.return_value = SAMPLE_COMPANY_FACTS_JSON

    mock_get.side_effect = [tickers_response, facts_response]

    response = client.get("/api/v1/sec/analysis/AAPL")
    assert response.status_code == 200
    data = response.json()

    assert data["ticker"] == "AAPL"
    assert data["company_name"] == "Apple Inc."
    assert "analyzed_period" in data
    assert data["periods_analyzed_count"] > 0
    assert "anomaly_detection" in data
    assert "trend_classification" in data
    assert "historical_sequence" in data
    assert len(data["historical_sequence"]) > 0


@patch("httpx.Client.get")
def test_analyze_company_alias_endpoint_success(mock_get):
    tickers_response = MagicMock()
    tickers_response.status_code = 200
    tickers_response.json.return_value = SAMPLE_TICKERS_JSON

    facts_response = MagicMock()
    facts_response.status_code = 200
    facts_response.json.return_value = SAMPLE_COMPANY_FACTS_JSON

    mock_get.side_effect = [tickers_response, facts_response]

    response = client.get("/api/v1/sec/AAPL/analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"


@patch("httpx.Client.get")
def test_analytics_trends_and_anomalies_endpoint_success(mock_get):
    tickers_response = MagicMock()
    tickers_response.status_code = 200
    tickers_response.json.return_value = SAMPLE_TICKERS_JSON

    facts_response = MagicMock()
    facts_response.status_code = 200
    facts_response.json.return_value = SAMPLE_COMPANY_FACTS_JSON

    mock_get.side_effect = [tickers_response, facts_response]

    response = client.get("/api/v1/analytics/trends-and-anomalies?ticker=AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert "trend_classification" in data
    assert data["trend_classification"]["category"] in [
        "ACCELERATING_GROWTH",
        "STABLE_COMPOUNDER",
        "MARGIN_COMPRESSION",
        "HIGH_FINANCIAL_STRESS",
    ]


@patch("httpx.Client.get")
def test_analyze_company_endpoint_unknown_ticker(mock_get):
    tickers_response = MagicMock()
    tickers_response.status_code = 200
    tickers_response.json.return_value = SAMPLE_TICKERS_JSON
    mock_get.return_value = tickers_response

    response = client.get("/api/v1/sec/analysis/UNKNOWN")
    assert response.status_code == 404
    assert "not found in SEC EDGAR directory" in response.json()["detail"]


def test_analyze_company_endpoint_invalid_path():
    response = client.get("/api/v1/sec/analysis/TOOLONGTICKERNAME")
    assert response.status_code == 422


@patch("httpx.Client.get")
def test_analyze_company_endpoint_upstream_network_error(mock_get):
    tickers_response = MagicMock()
    tickers_response.status_code = 200
    tickers_response.json.return_value = SAMPLE_TICKERS_JSON

    mock_get.side_effect = [
        tickers_response,
        httpx.ConnectError("Failed to reach SEC facts service"),
    ]

    response = client.get("/api/v1/sec/analysis/AAPL")
    assert response.status_code == 502
    assert "Failed to fetch XBRL company facts" in response.json()["detail"]


@patch("httpx.Client.get")
def test_analyze_company_endpoint_sec_rate_limited(mock_get):
    tickers_response = MagicMock()
    tickers_response.status_code = 200
    tickers_response.json.return_value = SAMPLE_TICKERS_JSON

    rate_limit_response = MagicMock()
    rate_limit_response.status_code = 429

    mock_get.side_effect = [
        tickers_response,
        rate_limit_response,
    ]

    response = client.get("/api/v1/sec/analysis/AAPL")
    assert response.status_code == 429
    assert "rate limit exceeded" in response.json()["detail"]
