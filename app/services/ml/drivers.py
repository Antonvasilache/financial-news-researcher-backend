from app.core.math_utils import format_percentage, format_ratio
from app.schemas.ml import FeatureImpact, FinancialTrendCategory

TREND_LABELS: dict[FinancialTrendCategory, str] = {
    FinancialTrendCategory.ACCELERATING_GROWTH: "Accelerating Growth",
    FinancialTrendCategory.STABLE_COMPOUNDER: "Stable Compounder",
    FinancialTrendCategory.MARGIN_COMPRESSION: "Margin Compression",
    FinancialTrendCategory.HIGH_FINANCIAL_STRESS: "High Financial Stress",
}

TREND_SUMMARIES: dict[FinancialTrendCategory, str] = {
    FinancialTrendCategory.ACCELERATING_GROWTH: (
        "Strong top-line acceleration coupled with expanding or elevated operating margins "
        "and prudent leverage."
    ),
    FinancialTrendCategory.STABLE_COMPOUNDER: (
        "Consistent profitability margins, balanced leverage, predictable operational cash flow, "
        "and steady compounded growth."
    ),
    FinancialTrendCategory.MARGIN_COMPRESSION: (
        "Top-line revenue remains resilient or positive, but operating and gross margins are "
        "eroding due to escalating operating expenses or cost of revenue."
    ),
    FinancialTrendCategory.HIGH_FINANCIAL_STRESS: (
        "Compounded financial headwinds characterized by negative operating margins, "
        "working capital deficit, or escalating leverage relative to cash flow."
    ),
}


def generate_key_drivers(
    category: FinancialTrendCategory,
    feature_vector: dict[str, float],
) -> list[FeatureImpact]:
    """Generate human-readable key drivers explaining the predicted trend category."""
    drivers: list[FeatureImpact] = []

    rev_growth = feature_vector["revenue_growth_yoy"]
    drivers.append(
        FeatureImpact(
            feature_name="revenue_growth_yoy",
            label="Revenue Growth (YoY)",
            current_value=rev_growth,
            formatted_value=format_percentage(rev_growth),
            impact_direction="POSITIVE" if rev_growth > 0.05 else "NEGATIVE" if rev_growth < 0 else "NEUTRAL",
            description=(
                "Top-line expansion driving business scale."
                if rev_growth > 0.05
                else "Top-line revenue contraction or stagnation."
                if rev_growth < 0
                else "Moderate stable top-line trajectory."
            ),
        )
    )

    op_margin = feature_vector["operating_margin"]
    drivers.append(
        FeatureImpact(
            feature_name="operating_margin",
            label="Operating Margin (EBIT)",
            current_value=op_margin,
            formatted_value=format_percentage(op_margin),
            impact_direction="POSITIVE" if op_margin > 0.15 else "NEGATIVE" if op_margin < 0.05 else "NEUTRAL",
            description=(
                "Robust operating efficiency and pricing power."
                if op_margin > 0.15
                else "Eroded or negative operating margin reflecting cost pressures."
                if op_margin < 0.05
                else "Balanced operating profitability in line with market averages."
            ),
        )
    )

    op_margin_delta = feature_vector["operating_margin_delta"]
    drivers.append(
        FeatureImpact(
            feature_name="operating_margin_delta",
            label="Operating Margin Delta",
            current_value=op_margin_delta,
            formatted_value=format_percentage(op_margin_delta),
            impact_direction="POSITIVE" if op_margin_delta > 0.01 else "NEGATIVE" if op_margin_delta < -0.02 else "NEUTRAL",
            description=(
                "Expanding operating margin trajectory."
                if op_margin_delta > 0.01
                else "Noticeable operating margin contraction period-over-period."
                if op_margin_delta < -0.02
                else "Stable margin stability across consecutive periods."
            ),
        )
    )

    curr_ratio = feature_vector["current_ratio"]
    drivers.append(
        FeatureImpact(
            feature_name="current_ratio",
            label="Current Liquidity Ratio",
            current_value=curr_ratio,
            formatted_value=format_ratio(curr_ratio),
            impact_direction="POSITIVE" if curr_ratio >= 1.3 else "NEGATIVE" if curr_ratio < 1.0 else "NEUTRAL",
            description=(
                "Comfortable liquidity buffer covering short-term obligations."
                if curr_ratio >= 1.3
                else "Tight working capital ratio below unity."
                if curr_ratio < 1.0
                else "Adequate baseline liquidity."
            ),
        )
    )

    debt_to_equity = feature_vector["debt_to_equity"]
    drivers.append(
        FeatureImpact(
            feature_name="debt_to_equity",
            label="Debt to Equity Ratio",
            current_value=debt_to_equity,
            formatted_value=format_ratio(debt_to_equity),
            impact_direction="POSITIVE" if debt_to_equity <= 1.2 else "NEGATIVE" if debt_to_equity > 2.5 else "NEUTRAL",
            description=(
                "Conservative debt leverage maintaining financial flexibility."
                if debt_to_equity <= 1.2
                else "Elevated debt burden amplifying balance sheet risk."
                if debt_to_equity > 2.5
                else "Moderate manageable leverage profile."
            ),
        )
    )

    return drivers
