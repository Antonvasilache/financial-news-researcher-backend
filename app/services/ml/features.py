from app.core.math_utils import calculate_growth_rate, safe_float
from app.schemas.financials import PeriodFinancials

FEATURE_NAMES: list[str] = [
    "revenue_growth_yoy",
    "operating_margin",
    "gross_margin",
    "net_margin",
    "current_ratio",
    "debt_to_equity",
    "operating_margin_delta",
    "gross_margin_delta",
    "revenue_to_debt_divergence",
    "cash_flow_to_net_income",
    "working_capital_to_assets",
]

DEFAULT_FEATURE_VALUES: dict[str, float] = {
    "revenue_growth_yoy": 0.05,
    "operating_margin": 0.12,
    "gross_margin": 0.35,
    "net_margin": 0.08,
    "current_ratio": 1.5,
    "debt_to_equity": 1.0,
    "operating_margin_delta": 0.0,
    "gross_margin_delta": 0.0,
    "revenue_to_debt_divergence": 0.0,
    "cash_flow_to_net_income": 1.0,
    "working_capital_to_assets": 0.15,
}


def extract_feature_vector(
    current_period: PeriodFinancials,
    previous_period: PeriodFinancials | None,
) -> dict[str, float]:
    """Compute the standardized 11-dimensional feature map for a target period."""
    # 1. Revenue growth (prefer YoY, fallback to period-over-period)
    revenue_growth_yoy = current_period.ratios.revenue_growth_yoy
    if revenue_growth_yoy is None and previous_period is not None:
        revenue_growth_yoy = calculate_growth_rate(
            current_period.metrics.revenue, previous_period.metrics.revenue
        )

    # 2-6. Core ratios
    operating_margin = current_period.ratios.operating_margin
    gross_margin = current_period.ratios.gross_margin
    net_margin = current_period.ratios.net_margin
    current_ratio = current_period.ratios.current_ratio
    debt_to_equity = current_period.ratios.debt_to_equity

    # 7-8. Margin deltas from previous period
    operating_margin_delta = 0.0
    gross_margin_delta = 0.0
    if previous_period is not None:
        if (
            operating_margin is not None
            and previous_period.ratios.operating_margin is not None
        ):
            operating_margin_delta = (
                operating_margin - previous_period.ratios.operating_margin
            )
        if gross_margin is not None and previous_period.ratios.gross_margin is not None:
            gross_margin_delta = gross_margin - previous_period.ratios.gross_margin

    # 9. Revenue-to-debt growth divergence
    revenue_to_debt_divergence = 0.0
    if previous_period is not None:
        debt_growth = calculate_growth_rate(
            current_period.metrics.total_debt, previous_period.metrics.total_debt
        )
        if debt_growth is not None:
            effective_revenue_growth = (
                revenue_growth_yoy
                if revenue_growth_yoy is not None
                else DEFAULT_FEATURE_VALUES["revenue_growth_yoy"]
            )
            revenue_to_debt_divergence = debt_growth - effective_revenue_growth

    # 10. Cash flow to net income
    net_income = current_period.metrics.net_income
    cash_flow = current_period.metrics.operating_cash_flow
    cash_flow_to_net_income = 1.0
    if net_income is not None and cash_flow is not None and abs(net_income) > 1e-9:
        cash_flow_to_net_income = cash_flow / abs(net_income)

    # 11. Working capital to total assets
    current_assets = current_period.metrics.current_assets
    current_liabilities = current_period.metrics.current_liabilities
    total_assets = current_period.metrics.total_assets
    working_capital_to_assets = 0.15
    if (
        current_assets is not None
        and current_liabilities is not None
        and total_assets is not None
        and total_assets > 1e-9
    ):
        working_capital_to_assets = (current_assets - current_liabilities) / total_assets

    features_map = {
        "revenue_growth_yoy": safe_float(
            revenue_growth_yoy, DEFAULT_FEATURE_VALUES["revenue_growth_yoy"]
        ),
        "operating_margin": safe_float(
            operating_margin, DEFAULT_FEATURE_VALUES["operating_margin"]
        ),
        "gross_margin": safe_float(
            gross_margin, DEFAULT_FEATURE_VALUES["gross_margin"]
        ),
        "net_margin": safe_float(
            net_margin, DEFAULT_FEATURE_VALUES["net_margin"]
        ),
        "current_ratio": safe_float(
            current_ratio, DEFAULT_FEATURE_VALUES["current_ratio"]
        ),
        "debt_to_equity": safe_float(
            debt_to_equity, DEFAULT_FEATURE_VALUES["debt_to_equity"]
        ),
        "operating_margin_delta": safe_float(
            operating_margin_delta, DEFAULT_FEATURE_VALUES["operating_margin_delta"]
        ),
        "gross_margin_delta": safe_float(
            gross_margin_delta, DEFAULT_FEATURE_VALUES["gross_margin_delta"]
        ),
        "revenue_to_debt_divergence": safe_float(
            revenue_to_debt_divergence,
            DEFAULT_FEATURE_VALUES["revenue_to_debt_divergence"],
        ),
        "cash_flow_to_net_income": safe_float(
            cash_flow_to_net_income, DEFAULT_FEATURE_VALUES["cash_flow_to_net_income"]
        ),
        "working_capital_to_assets": safe_float(
            working_capital_to_assets,
            DEFAULT_FEATURE_VALUES["working_capital_to_assets"],
        ),
    }
    return features_map
