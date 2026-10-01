from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.financial_metrics import FinancialMetricsService, safe_divide

client = TestClient(app)

SAMPLE_TICKERS_JSON = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 1318605, "ticker": "TSLA", "title": "Tesla, Inc."},
}

SAMPLE_COMPANY_FACTS_JSON = {
    "cik": 320193,
    "entityName": "Apple Inc.",
    "facts": {
        "us-gaap": {
            "Revenues": {
                "label": "Revenues",
                "units": {
                    "USD": [
                        {
                            "end": "2022-09-24",
                            "val": 394328000000.0,
                            "fy": 2022,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2022-10-28",
                        },
                        {
                            "end": "2023-09-30",
                            "val": 383285000000.0,
                            "fy": 2023,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2023-11-03",
                        },
                        {
                            "end": "2024-09-28",
                            "val": 391035000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        },
                        {
                            "start": "2023-04-02",
                            "end": "2023-07-01",
                            "val": 81797000000.0,
                            "fy": 2023,
                            "fp": "Q3",
                            "form": "10-Q",
                            "filed": "2023-08-04",
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
                        # 9-month YTD figure that should be filtered out from single quarter metrics
                        {
                            "start": "2023-10-01",
                            "end": "2024-06-29",
                            "val": 296000000000.0,
                            "fy": 2024,
                            "fp": "Q3",
                            "form": "10-Q",
                            "filed": "2024-08-02",
                        },
                    ]
                },
            },
            "CostOfGoodsAndServicesSold": {
                "units": {
                    "USD": [
                        {
                            "end": "2023-09-30",
                            "val": 214137000000.0,
                            "fy": 2023,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2023-11-03",
                        },
                        {
                            "end": "2024-09-28",
                            "val": 210352000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        },
                    ]
                }
            },
            "GrossProfit": {
                "units": {
                    "USD": [
                        {
                            "end": "2023-09-30",
                            "val": 169148000000.0,
                            "fy": 2023,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2023-11-03",
                        },
                        {
                            "end": "2024-09-28",
                            "val": 180683000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        },
                    ]
                }
            },
            "OperatingIncomeLoss": {
                "units": {
                    "USD": [
                        {
                            "end": "2023-09-30",
                            "val": 114301000000.0,
                            "fy": 2023,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2023-11-03",
                        },
                        {
                            "end": "2024-09-28",
                            "val": 123216000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        },
                    ]
                }
            },
            "NetIncomeLoss": {
                "units": {
                    "USD": [
                        {
                            "end": "2022-09-24",
                            "val": 99803000000.0,
                            "fy": 2022,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2022-10-28",
                        },
                        {
                            "end": "2023-09-30",
                            "val": 96995000000.0,
                            "fy": 2023,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2023-11-03",
                        },
                        {
                            "end": "2024-09-28",
                            "val": 93736000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        },
                        {
                            "start": "2023-04-02",
                            "end": "2023-07-01",
                            "val": 19881000000.0,
                            "fy": 2023,
                            "fp": "Q3",
                            "form": "10-Q",
                            "filed": "2023-08-04",
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
                            "end": "2024-09-28",
                            "val": 152985000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        }
                    ]
                }
            },
            "LiabilitiesCurrent": {
                "units": {
                    "USD": [
                        {
                            "end": "2024-09-28",
                            "val": 176392000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        }
                    ]
                }
            },
            "Assets": {
                "units": {
                    "USD": [
                        {
                            "end": "2024-09-28",
                            "val": 364980000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        }
                    ]
                }
            },
            "StockholdersEquity": {
                "units": {
                    "USD": [
                        {
                            "end": "2024-09-28",
                            "val": 66885000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        }
                    ]
                }
            },
            "LongTermDebtNoncurrent": {
                "units": {
                    "USD": [
                        {
                            "end": "2024-09-28",
                            "val": 96603000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        }
                    ]
                }
            },
            "CashAndCashEquivalentsAtCarryingValue": {
                "units": {
                    "USD": [
                        {
                            "end": "2024-09-28",
                            "val": 29942000000.0,
                            "fy": 2024,
                            "fp": "FY",
                            "form": "10-K",
                            "filed": "2024-11-01",
                        }
                    ]
                }
            },
        }
    },
}


def test_safe_divide():
    assert safe_divide(100.0, 200.0) == 0.5
    assert safe_divide(10.0, 0.0) is None
    assert safe_divide(None, 100.0) is None
    assert safe_divide(100.0, None) is None
    assert safe_divide(1.0, 3.0, decimal_places=2) == 0.33


def test_extract_company_financials_annual_and_quarterly():
    service = FinancialMetricsService()
    result = service.extract_company_financials(
        facts_data=SAMPLE_COMPANY_FACTS_JSON,
        ticker="AAPL",
        cik="0000320193",
        company_name="Apple Inc.",
    )

    assert result.ticker == "AAPL"
    assert result.cik == "0000320193"
    assert result.company_name == "Apple Inc."
    assert len(result.annual_reports) == 3

    # Check newest annual period first (FY2024)
    fy24 = result.annual_reports[0]
    assert fy24.period == "FY2024"
    assert fy24.fiscal_year == 2024
    assert fy24.metrics.revenue == 391035000000.0
    assert fy24.metrics.cost_of_revenue == 210352000000.0
    assert fy24.metrics.gross_profit == 180683000000.0
    assert fy24.metrics.operating_income == 123216000000.0
    assert fy24.metrics.net_income == 93736000000.0
    assert fy24.metrics.current_assets == 152985000000.0
    assert fy24.metrics.current_liabilities == 176392000000.0
    assert fy24.metrics.stockholders_equity == 66885000000.0
    assert fy24.metrics.total_debt == 96603000000.0

    # Total liabilities derived from Assets - StockholdersEquity
    assert fy24.metrics.total_liabilities == 364980000000.0 - 66885000000.0

    # Ratios verification for FY2024
    # Gross Margin: 180683 / 391035 = 0.4621
    assert fy24.ratios.gross_margin == pytest.approx(0.4621, abs=0.001)
    # Operating Margin: 123216 / 391035 = 0.3151
    assert fy24.ratios.operating_margin == pytest.approx(0.3151, abs=0.001)
    # Net Margin: 93736 / 391035 = 0.2397
    assert fy24.ratios.net_margin == pytest.approx(0.2397, abs=0.001)
    # Current Ratio: 152985 / 176392 = 0.8673
    assert fy24.ratios.current_ratio == pytest.approx(0.8673, abs=0.001)
    # Debt to Equity: 96603 / 66885 = 1.4443
    assert fy24.ratios.debt_to_equity == pytest.approx(1.4443, abs=0.001)
    # Return on Equity: 93736 / 66885 = 1.4014
    assert fy24.ratios.return_on_equity == pytest.approx(1.4014, abs=0.001)

    # YoY Revenue growth in FY2024: (391035 - 383285) / 383285 = +0.0202 (+2.02%)
    assert fy24.ratios.revenue_growth_yoy == pytest.approx(0.0202, abs=0.0005)

    # FY2023 Revenue growth: (383285 - 394328) / 394328 = -0.0280 (-2.8%)
    fy23 = result.annual_reports[1]
    assert fy23.period == "FY2023"
    assert fy23.ratios.revenue_growth_yoy == pytest.approx(-0.0280, abs=0.0005)

    # Quarterly reports verification
    assert len(result.quarterly_reports) == 2
    q24 = result.quarterly_reports[0]
    assert q24.period == "2024-Q3"
    assert q24.metrics.revenue == 85777000000.0
    assert q24.metrics.net_income == 21448000000.0

    # YoY Revenue growth for 2024-Q3 compared to 2023-Q3:
    # (85777 - 81797) / 81797 = +0.0487 (+4.87%)
    assert q24.ratios.revenue_growth_yoy == pytest.approx(0.0487, abs=0.0005)


def test_derive_missing_gross_profit_and_cost():
    service = FinancialMetricsService()
    incomplete_facts = {
        "cik": 123456,
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {
                        "USD": [
                            {
                                "end": "2024-12-31",
                                "val": 1000000.0,
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2025-01-15",
                            }
                        ]
                    }
                },
                "CostOfRevenue": {
                    "units": {
                        "USD": [
                            {
                                "end": "2024-12-31",
                                "val": 600000.0,
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2025-01-15",
                            }
                        ]
                    }
                },
            }
        },
    }

    result = service.extract_company_financials(
        facts_data=incomplete_facts,
        ticker="TEST",
        cik="0000123456",
        company_name="Test Corp",
    )

    assert len(result.annual_reports) == 1
    period = result.annual_reports[0]
    assert period.metrics.revenue == 1000000.0
    assert period.metrics.cost_of_revenue == 600000.0
    # Gross profit should be derived: 1000000 - 600000 = 400000
    assert period.metrics.gross_profit == 400000.0
    assert period.ratios.gross_margin == 0.4


def mock_dispatcher(url: str, **kwargs):
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    if "company_tickers.json" in url:
        mock_resp.json.return_value = SAMPLE_TICKERS_JSON
    elif "api/xbrl/companyfacts/CIK0000320193.json" in url:
        mock_resp.json.return_value = SAMPLE_COMPANY_FACTS_JSON
    else:
        mock_resp.status_code = 404
        mock_resp.text = "Not found"
    return mock_resp


@patch("httpx.Client.get", side_effect=mock_dispatcher)
def test_get_financials_endpoint_success(mock_get):
    response = client.get("/api/v1/sec/financials/AAPL?annual_limit=3&quarterly_limit=5")
    assert response.status_code == 200
    data = response.json()

    assert data["ticker"] == "AAPL"
    assert data["cik"] == "0000320193"
    assert data["company_name"] == "Apple Inc."
    assert len(data["annual_reports"]) == 3
    assert len(data["quarterly_reports"]) == 2

    # Check that highest level metrics and calculated ratios exist
    latest_annual = data["annual_reports"][0]
    assert latest_annual["fiscal_year"] == 2024
    assert latest_annual["metrics"]["revenue"] == 391035000000.0
    assert latest_annual["ratios"]["gross_margin"] is not None
    assert latest_annual["ratios"]["operating_margin"] is not None
    assert latest_annual["ratios"]["return_on_equity"] is not None


@patch("httpx.Client.get", side_effect=mock_dispatcher)
def test_get_financials_endpoint_unknown_ticker(mock_get):
    response = client.get("/api/v1/sec/financials/NOTFOUND")
    assert response.status_code == 404
    assert "not found in SEC EDGAR directory" in response.json()["detail"]


def test_get_financials_endpoint_invalid_ticker_path():
    # Ticker longer than 10 chars fails Path validation with 422
    response = client.get("/api/v1/sec/financials/TOOLONGTICKERNAME")
    assert response.status_code == 422


@patch("httpx.Client.get")
def test_get_financials_endpoint_sec_network_error(mock_get):
    tickers_resp = MagicMock()
    tickers_resp.status_code = 200
    tickers_resp.json.return_value = SAMPLE_TICKERS_JSON

    mock_get.side_effect = [
        tickers_resp,
        httpx.ConnectError("Failed to reach SEC facts service"),
    ]

    response = client.get("/api/v1/sec/financials/AAPL")
    assert response.status_code == 502
    assert "Failed to fetch XBRL company facts" in response.json()["detail"]


@patch("httpx.Client.get")
def test_get_financials_endpoint_sec_rate_limited(mock_get):
    tickers_resp = MagicMock()
    tickers_resp.status_code = 200
    tickers_resp.json.return_value = SAMPLE_TICKERS_JSON

    rate_limit_resp = MagicMock()
    rate_limit_resp.status_code = 429

    mock_get.side_effect = [
        tickers_resp,
        rate_limit_resp,
    ]

    response = client.get("/api/v1/sec/financials/AAPL")
    assert response.status_code == 429
    assert "rate limit exceeded" in response.json()["detail"]


def test_non_consecutive_years_yoy_growth_is_none():
    service = FinancialMetricsService()
    facts_with_gap = {
        "cik": 123456,
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {
                                "end": "2021-12-31",
                                "val": 1000000.0,
                                "fy": 2021,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2022-01-15",
                            },
                            {
                                "end": "2024-12-31",
                                "val": 1500000.0,
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2025-01-15",
                            },
                        ]
                    }
                }
            }
        },
    }

    result = service.extract_company_financials(
        facts_data=facts_with_gap,
        ticker="GAP",
        cik="0000123456",
        company_name="Gap Corp",
    )

    assert len(result.annual_reports) == 2
    # 2024 is preceded by 2021, not 2023. YoY 1-year growth must be None!
    report_2024 = result.annual_reports[0]
    assert report_2024.fiscal_year == 2024
    assert report_2024.ratios.revenue_growth_yoy is None


def test_negative_stockholders_equity_roe_is_none():
    service = FinancialMetricsService()
    negative_equity_facts = {
        "cik": 999999,
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"end": "2024-12-31", "val": 5000000.0, "fy": 2024, "fp": "FY", "form": "10-K", "filed": "2025-01-15"}
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {"end": "2024-12-31", "val": 1000000.0, "fy": 2024, "fp": "FY", "form": "10-K", "filed": "2025-01-15"}
                        ]
                    }
                },
                "StockholdersEquity": {
                    "units": {
                        "USD": [
                            {"end": "2024-12-31", "val": -250000.0, "fy": 2024, "fp": "FY", "form": "10-K", "filed": "2025-01-15"}
                        ]
                    }
                },
            }
        },
    }

    result = service.extract_company_financials(
        facts_data=negative_equity_facts,
        ticker="NEG",
        cik="0000999999",
        company_name="Negative Equity Corp",
    )

    report = result.annual_reports[0]
    assert report.metrics.stockholders_equity == -250000.0
    # ROE must be None for negative equity
    assert report.ratios.return_on_equity is None


def test_bidirectional_equity_derivation():
    service = FinancialMetricsService()
    facts_no_equity = {
        "cik": 888888,
        "facts": {
            "us-gaap": {
                "Assets": {
                    "units": {
                        "USD": [
                            {"end": "2024-12-31", "val": 1000000.0, "fy": 2024, "fp": "FY", "form": "10-K", "filed": "2025-01-15"}
                        ]
                    }
                },
                "Liabilities": {
                    "units": {
                        "USD": [
                            {"end": "2024-12-31", "val": 400000.0, "fy": 2024, "fp": "FY", "form": "10-K", "filed": "2025-01-15"}
                        ]
                    }
                },
            }
        },
    }

    result = service.extract_company_financials(
        facts_data=facts_no_equity,
        ticker="EQDERIV",
        cik="0000888888",
        company_name="Equity Derivation Corp",
    )

    report = result.annual_reports[0]
    assert report.metrics.total_assets == 1000000.0
    assert report.metrics.total_liabilities == 400000.0
    # Equity derived: 1,000,000 - 400,000 = 600,000
    assert report.metrics.stockholders_equity == 600000.0

