import logging
import math
from datetime import date
from typing import Any

from app.schemas.financials import (
    CompanyFinancialsResponse,
    FinancialRatios,
    FinancialStatementMetrics,
    PeriodFinancials,
)

logger = logging.getLogger(__name__)

# Standard US-GAAP concept tag candidates in priority order
CONCEPT_CANDIDATES: dict[str, list[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueGoodsNet",
        "TotalRevenuesAndOtherIncome",
    ],
    "cost_of_revenue": [
        "CostOfGoodsAndServicesSold",
        "CostOfRevenue",
        "CostOfGoodsSold",
    ],
    "gross_profit": [
        "GrossProfit",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
    ],
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
    ],
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
    ],
    "current_assets": [
        "AssetsCurrent",
    ],
    "total_assets": [
        "Assets",
    ],
    "current_liabilities": [
        "LiabilitiesCurrent",
    ],
    "total_liabilities": [
        "Liabilities",
    ],
    "stockholders_equity": [
        "StockholdersEquity",
        "CommonStockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "cash_and_equivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    "total_debt": [
        "LongTermDebtNoncurrent",
        "LongTermDebt",
        "DebtInstrumentCarryingAmount",
        "DebtCurrent",
        "ShortTermBorrowings",
        "CommercialPaper",
    ],
    "eps": [
        "EarningsPerShareDiluted",
        "EarningsPerShareBasic",
    ],
}

DURATION_METRICS: set[str] = {
    "revenue",
    "cost_of_revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "operating_cash_flow",
    "eps",
}


def safe_divide(
    numerator: float | None, denominator: float | None, decimal_places: int = 4
) -> float | None:
    """Safely divide two numbers handling None, zero, non-finite values, and rounding."""
    if numerator is None or denominator is None:
        return None
    if not math.isfinite(numerator) or not math.isfinite(denominator):
        return None
    if abs(denominator) < 1e-9:
        return None
    return round(numerator / denominator, decimal_places)


def calculate_growth_rate(
    current_value: float | None,
    previous_value: float | None,
    decimal_places: int = 4,
) -> float | None:
    """Safely calculate percentage growth handling negative bases, non-finite values, and zero bases."""
    if current_value is None or previous_value is None:
        return None
    if not math.isfinite(current_value) or not math.isfinite(previous_value):
        return None
    if abs(previous_value) < 1e-9:
        return None
    return round((current_value - previous_value) / abs(previous_value), decimal_places)


def parse_date_safe(date_string: str | None) -> date | None:
    """Parse YYYY-MM-DD date string safely."""
    if not date_string:
        return None
    try:
        return date.fromisoformat(date_string[:10])
    except (ValueError, TypeError):
        return None


class FinancialMetricsService:
    """Service to process SEC EDGAR XBRL facts and compute financial metrics and ratios."""

    def extract_company_financials(
        self,
        facts_data: dict[str, Any],
        ticker: str,
        cik: str,
        company_name: str,
        annual_limit: int = 5,
        quarterly_limit: int = 8,
    ) -> CompanyFinancialsResponse:
        """Extract multi-year annual and quarterly financials and calculate financial ratios."""
        us_gaap_facts = facts_data.get("facts", {}).get("us-gaap", {})

        # Extract metric raw observations mapped by concept and period
        annual_by_year: dict[int, dict[str, Any]] = {}
        quarterly_by_key: dict[tuple[int, str], dict[str, Any]] = {}

        for metric_name, tag_candidates in CONCEPT_CANDIDATES.items():
            for priority_index, candidate in enumerate(tag_candidates):
                if candidate not in us_gaap_facts:
                    continue
                records = self._get_units_records(us_gaap_facts[candidate])
                if not records:
                    continue

                for item in records:
                    try:
                        raw_val = item.get("val")
                        if raw_val is None:
                            continue
                        value = float(raw_val)

                        fiscal_year_raw = item.get("fy")
                        if fiscal_year_raw is None:
                            continue
                        fiscal_year = int(fiscal_year_raw)

                        fiscal_period = str(item.get("fp", "")).strip().upper()
                        form = str(item.get("form", "")).strip().upper()
                        end_date = str(item.get("end", "")).strip()
                        filed_date = str(item.get("filed", "")).strip()
                        start_date = str(item.get("start", "")).strip() if item.get("start") else None

                        # Check Annual Report: Must be from a 10-K filing (not a 10-Q)
                        is_annual = (form in ("10-K", "10-K/A")) or (
                            fiscal_period == "FY" and form not in ("10-Q", "10-Q/A")
                        )
                        if is_annual and fiscal_period not in ("Q1", "Q2", "Q3"):
                            self._record_annual_metric(
                                annual_by_year=annual_by_year,
                                fiscal_year=fiscal_year,
                                metric_name=metric_name,
                                value=value,
                                end_date=end_date,
                                filed_date=filed_date,
                                form=form or "10-K",
                                priority_index=priority_index,
                            )

                        # Check Quarterly Report: From 10-Q for Q1, Q2, Q3
                        elif form in ("10-Q", "10-Q/A") and fiscal_period in ("Q1", "Q2", "Q3"):
                            # If duration metric, verify it is a single-quarter figure (~90 days, < 115 days)
                            if metric_name in DURATION_METRICS and start_date and end_date:
                                start_dt = parse_date_safe(start_date)
                                end_dt = parse_date_safe(end_date)
                                if start_dt and end_dt:
                                    duration_days = (end_dt - start_dt).days
                                    if duration_days > 115:
                                        continue  # Skip 6-month or 9-month YTD cumulative record

                            self._record_quarterly_metric(
                                quarterly_by_key=quarterly_by_key,
                                fiscal_year=fiscal_year,
                                fiscal_period=fiscal_period,
                                metric_name=metric_name,
                                value=value,
                                end_date=end_date,
                                filed_date=filed_date,
                                form=form or "10-Q",
                                priority_index=priority_index,
                            )

                    except (ValueError, TypeError) as parse_error:
                        logger.debug("Failed parsing fact record for %s: %s", metric_name, parse_error)
                        continue

        annual_reports = self._build_annual_periods(annual_by_year, annual_limit)
        quarterly_reports = self._build_quarterly_periods(quarterly_by_key, quarterly_limit)

        return CompanyFinancialsResponse(
            ticker=ticker.upper(),
            cik=cik,
            company_name=company_name,
            annual_reports=annual_reports,
            quarterly_reports=quarterly_reports,
        )

    def _get_units_records(self, concept_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Get unit entries (USD or USD/shares) from a concept object."""
        units = concept_data.get("units", {})
        if units.get("USD"):
            return units["USD"]
        if units.get("USD/shares"):
            return units["USD/shares"]
        return []

    def _record_annual_metric(
        self,
        annual_by_year: dict[int, dict[str, Any]],
        fiscal_year: int,
        metric_name: str,
        value: float,
        end_date: str,
        filed_date: str,
        form: str,
        priority_index: int = 0,
    ) -> None:
        if fiscal_year not in annual_by_year:
            annual_by_year[fiscal_year] = {
                "fiscal_year": fiscal_year,
                "fiscal_period": "FY",
                "end_date": end_date,
                "filed_date": filed_date,
                "form": form,
                "metrics": {},
                "_filed_dates": {},
                "_priorities": {},
                "_end_dates": {},
            }
        period_entry = annual_by_year[fiscal_year]

        existing_priority = period_entry["_priorities"].get(metric_name, 999)
        existing_filed = period_entry["_filed_dates"].get(metric_name, "")
        existing_end = period_entry.get("_end_dates", {}).get(metric_name, "")

        should_update = False
        if metric_name not in period_entry["metrics"]:
            should_update = True
        elif priority_index < existing_priority:
            should_update = True
        elif priority_index == existing_priority:
            if filed_date > existing_filed:
                should_update = True
            elif filed_date == existing_filed:
                # If filing dates match (e.g. beginning vs end of period cash in same 10-K),
                # prefer the entry with the latest end_date to avoid rolling back to beginning of year
                should_update = bool(end_date and end_date >= existing_end)

        if should_update:
            period_entry["metrics"][metric_name] = value
            period_entry["_priorities"][metric_name] = priority_index
            period_entry["_filed_dates"][metric_name] = filed_date
            period_entry.setdefault("_end_dates", {})[metric_name] = end_date
            if filed_date > period_entry.get("filed_date", ""):
                period_entry["filed_date"] = filed_date
            if end_date and end_date > period_entry.get("end_date", ""):
                period_entry["end_date"] = end_date

    def _record_quarterly_metric(
        self,
        quarterly_by_key: dict[tuple[int, str], dict[str, Any]],
        fiscal_year: int,
        fiscal_period: str,
        metric_name: str,
        value: float,
        end_date: str,
        filed_date: str,
        form: str,
        priority_index: int = 0,
    ) -> None:
        period_key = (fiscal_year, fiscal_period)
        if period_key not in quarterly_by_key:
            quarterly_by_key[period_key] = {
                "fiscal_year": fiscal_year,
                "fiscal_period": fiscal_period,
                "end_date": end_date,
                "filed_date": filed_date,
                "form": form,
                "metrics": {},
                "_filed_dates": {},
                "_priorities": {},
                "_end_dates": {},
            }
        period_entry = quarterly_by_key[period_key]

        existing_priority = period_entry["_priorities"].get(metric_name, 999)
        existing_filed = period_entry["_filed_dates"].get(metric_name, "")
        existing_end = period_entry.get("_end_dates", {}).get(metric_name, "")

        should_update = False
        if metric_name not in period_entry["metrics"]:
            should_update = True
        elif priority_index < existing_priority:
            should_update = True
        elif priority_index == existing_priority:
            if filed_date > existing_filed:
                should_update = True
            elif filed_date == existing_filed:
                should_update = bool(end_date and end_date >= existing_end)

        if should_update:
            period_entry["metrics"][metric_name] = value
            period_entry["_priorities"][metric_name] = priority_index
            period_entry["_filed_dates"][metric_name] = filed_date
            period_entry.setdefault("_end_dates", {})[metric_name] = end_date
            if filed_date > period_entry.get("filed_date", ""):
                period_entry["filed_date"] = filed_date
            if end_date and end_date > period_entry.get("end_date", ""):
                period_entry["end_date"] = end_date

    def _derive_missing_metrics(self, metrics: dict[str, float]) -> None:
        """Derive standard missing line items from fundamental accounting relationships."""
        revenue = metrics.get("revenue")
        cost = metrics.get("cost_of_revenue")
        gross_profit = metrics.get("gross_profit")
        total_assets = metrics.get("total_assets")
        stockholders_equity = metrics.get("stockholders_equity")
        total_liabilities = metrics.get("total_liabilities")

        # Gross Profit = Revenue - Cost of Revenue
        if gross_profit is None and revenue is not None and cost is not None:
            metrics["gross_profit"] = round(revenue - cost, 2)

        # Cost of Revenue = Revenue - Gross Profit
        if cost is None and revenue is not None and gross_profit is not None:
            metrics["cost_of_revenue"] = round(revenue - gross_profit, 2)

        # Liabilities = Assets - Equity
        if (
            total_liabilities is None
            and total_assets is not None
            and stockholders_equity is not None
        ):
            metrics["total_liabilities"] = round(total_assets - stockholders_equity, 2)

        # Equity = Assets - Liabilities (bidirectional derivation)
        if (
            stockholders_equity is None
            and total_assets is not None
            and total_liabilities is not None
        ):
            metrics["stockholders_equity"] = round(total_assets - total_liabilities, 2)

    def _compute_ratios(self, metrics: dict[str, float]) -> FinancialRatios:
        """Calculate standard financial ratios from financial metrics."""
        revenue = metrics.get("revenue")
        gross_profit = metrics.get("gross_profit")
        operating_income = metrics.get("operating_income")
        net_income = metrics.get("net_income")
        current_assets = metrics.get("current_assets")
        current_liabilities = metrics.get("current_liabilities")
        total_assets = metrics.get("total_assets")
        stockholders_equity = metrics.get("stockholders_equity")
        total_debt = metrics.get("total_debt")

        gross_margin = safe_divide(gross_profit, revenue)
        operating_margin = safe_divide(operating_income, revenue)
        net_margin = safe_divide(net_income, revenue)
        current_ratio = safe_divide(current_assets, current_liabilities)
        debt_to_equity = safe_divide(total_debt, stockholders_equity)
        debt_to_assets = safe_divide(total_debt, total_assets)

        # Return on Equity: Net Income / Stockholders' Equity
        # Institutional financial standard: ROE is None when equity is negative (e.g. Starbucks, Boeing due to buybacks)
        return_on_equity = (
            safe_divide(net_income, stockholders_equity)
            if stockholders_equity is not None and stockholders_equity > 0
            else None
        )
        return_on_assets = safe_divide(net_income, total_assets)

        return FinancialRatios(
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            net_margin=net_margin,
            current_ratio=current_ratio,
            debt_to_equity=debt_to_equity,
            debt_to_assets=debt_to_assets,
            return_on_equity=return_on_equity,
            return_on_assets=return_on_assets,
            revenue_growth_yoy=None,
            net_income_growth_yoy=None,
        )

    def _build_annual_periods(
        self, annual_by_year: dict[int, dict[str, Any]], limit: int
    ) -> list[PeriodFinancials]:
        """Build and calculate YoY metrics for annual reports sorted by fiscal year."""
        sorted_years = sorted(annual_by_year.keys())
        periods: list[PeriodFinancials] = []

        for year in sorted_years:
            raw_period = annual_by_year[year]
            raw_metrics = raw_period["metrics"]
            self._derive_missing_metrics(raw_metrics)

            ratios = self._compute_ratios(raw_metrics)

            # Compute YoY Growth compared to strictly consecutive previous fiscal year (year - 1)
            prior_year_period = annual_by_year.get(year - 1)
            if prior_year_period is not None:
                prev_metrics = prior_year_period["metrics"]
                ratios.revenue_growth_yoy = calculate_growth_rate(
                    raw_metrics.get("revenue"), prev_metrics.get("revenue")
                )
                ratios.net_income_growth_yoy = calculate_growth_rate(
                    raw_metrics.get("net_income"), prev_metrics.get("net_income")
                )

            period_obj = PeriodFinancials(
                period=f"FY{year}",
                fiscal_year=year,
                fiscal_period="FY",
                end_date=raw_period.get("end_date", f"{year}-12-31"),
                filed_date=raw_period.get("filed_date"),
                form=raw_period.get("form", "10-K"),
                metrics=FinancialStatementMetrics(**raw_metrics),
                ratios=ratios,
            )
            periods.append(period_obj)

        # Return latest periods first up to limit
        periods.reverse()
        return periods[:limit]

    def _build_quarterly_periods(
        self, quarterly_by_key: dict[tuple[int, str], dict[str, Any]], limit: int
    ) -> list[PeriodFinancials]:
        """Build and calculate YoY metrics for quarterly reports."""
        # Sort chronologically by (fiscal_year, fiscal_period)
        sorted_keys = sorted(
            quarterly_by_key.keys(),
            key=lambda key: (key[0], key[1]),
        )
        periods: list[PeriodFinancials] = []
        quarter_end_map = {"Q1": "03-31", "Q2": "06-30", "Q3": "09-30"}

        for fiscal_year, fiscal_period in sorted_keys:
            raw_period = quarterly_by_key[(fiscal_year, fiscal_period)]
            raw_metrics = raw_period["metrics"]
            self._derive_missing_metrics(raw_metrics)

            ratios = self._compute_ratios(raw_metrics)

            # Compare to same quarter of previous year (fiscal_year - 1, fiscal_period)
            prev_quarter_key = (fiscal_year - 1, fiscal_period)
            if prev_quarter_key in quarterly_by_key:
                prev_metrics = quarterly_by_key[prev_quarter_key]["metrics"]
                ratios.revenue_growth_yoy = calculate_growth_rate(
                    raw_metrics.get("revenue"), prev_metrics.get("revenue")
                )
                ratios.net_income_growth_yoy = calculate_growth_rate(
                    raw_metrics.get("net_income"), prev_metrics.get("net_income")
                )

            fallback_date = f"{fiscal_year}-{quarter_end_map.get(fiscal_period, '12-31')}"
            resolved_end_date = raw_period.get("end_date") or fallback_date

            period_obj = PeriodFinancials(
                period=f"{fiscal_year}-{fiscal_period}",
                fiscal_year=fiscal_year,
                fiscal_period=fiscal_period,
                end_date=resolved_end_date,
                filed_date=raw_period.get("filed_date"),
                form=raw_period.get("form", "10-Q"),
                metrics=FinancialStatementMetrics(**raw_metrics),
                ratios=ratios,
            )
            periods.append(period_obj)

        # Return latest periods first up to limit
        periods.reverse()
        return periods[:limit]
