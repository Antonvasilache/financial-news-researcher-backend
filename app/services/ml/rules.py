from app.schemas.financials import PeriodFinancials
from app.schemas.ml import AnomalyDivergence


def detect_heuristic_divergences(
    current_period: PeriodFinancials,
    previous_period: PeriodFinancials | None,
    feature_vector: dict[str, float],
) -> list[AnomalyDivergence]:
    """Detect specific financial statement red flags and divergence patterns."""
    divergences: list[AnomalyDivergence] = []

    # 1. Margin Compression Divergence
    operating_margin_delta = feature_vector["operating_margin_delta"]
    revenue_growth = feature_vector["revenue_growth_yoy"]
    if operating_margin_delta <= -0.05:
        severity = (
            "SEVERE_ANOMALY"
            if (operating_margin_delta <= -0.08 or revenue_growth > 0.05)
            else "CAUTION"
        )
        context_clause = (
            f" despite top-line revenue expansion of {revenue_growth * 100:.1f}%"
            if revenue_growth > 0.05
            else ""
        )
        divergences.append(
            AnomalyDivergence(
                metric_name="operating_margin_delta",
                metric_label="Operating Margin Compression",
                current_value=feature_vector["operating_margin"],
                previous_value=(
                    previous_period.ratios.operating_margin
                    if previous_period
                    else None
                ),
                delta=operating_margin_delta,
                severity=severity,
                description=(
                    f"Operating margin compressed by {abs(operating_margin_delta) * 100:.1f}% period-over-period{context_clause}."
                ),
            )
        )

    # 2. Debt Escalation vs Revenue Growth Divergence
    revenue_debt_div = feature_vector["revenue_to_debt_divergence"]
    if revenue_debt_div >= 0.20:
        severity = "SEVERE_ANOMALY" if revenue_debt_div >= 0.35 else "CAUTION"
        divergences.append(
            AnomalyDivergence(
                metric_name="revenue_to_debt_divergence",
                metric_label="Debt Accumulation vs Revenue Divergence",
                current_value=current_period.metrics.total_debt,
                previous_value=(
                    previous_period.metrics.total_debt if previous_period else None
                ),
                delta=revenue_debt_div,
                severity=severity,
                description=(
                    f"Total debt growth outpaced revenue trajectory by {revenue_debt_div * 100:.1f}%, indicating leveraged balance sheet expansion."
                ),
            )
        )

    # 3. Cash Flow vs Net Income Divergence (Earnings Quality Red Flag)
    net_income = current_period.metrics.net_income
    cash_flow = current_period.metrics.operating_cash_flow
    if (
        net_income is not None
        and net_income > 0
        and cash_flow is not None
        and cash_flow < 0
    ):
        severity = (
            "SEVERE_ANOMALY" if abs(cash_flow) > 0.5 * net_income else "CAUTION"
        )
        divergences.append(
            AnomalyDivergence(
                metric_name="operating_cash_flow_divergence",
                metric_label="Negative Operating Cash Flow vs Net Income",
                current_value=cash_flow,
                previous_value=net_income,
                delta=cash_flow - net_income,
                severity=severity,
                description=(
                    f"Positive net income (${net_income:,.0f}) diverges sharply from negative operating cash flow (-${abs(cash_flow):,.0f}), indicating working capital drag or accrual quality divergence."
                ),
            )
        )

    # 4. Liquidity Deficit (Current Ratio < 1.0)
    current_ratio = current_period.ratios.current_ratio
    if current_ratio is not None and current_ratio < 1.0:
        severity = "SEVERE_ANOMALY" if current_ratio < 0.80 else "CAUTION"
        divergences.append(
            AnomalyDivergence(
                metric_name="current_ratio_liquidity",
                metric_label="Working Capital Deficit",
                current_value=current_ratio,
                previous_value=(
                    previous_period.ratios.current_ratio
                    if previous_period
                    else None
                ),
                delta=(
                    current_ratio - previous_period.ratios.current_ratio
                    if (
                        previous_period
                        and previous_period.ratios.current_ratio is not None
                    )
                    else None
                ),
                severity=severity,
                description=(
                    f"Current liquidity ratio of {current_ratio:.2f}x is below 1.0, signaling that current liabilities exceed current assets."
                ),
            )
        )

    # 5. Negative Stockholders' Equity / Extreme Solvency Risk
    equity = current_period.metrics.stockholders_equity
    if equity is not None and equity < 0:
        divergences.append(
            AnomalyDivergence(
                metric_name="negative_stockholders_equity",
                metric_label="Negative Stockholders' Equity",
                current_value=equity,
                previous_value=(
                    previous_period.metrics.stockholders_equity
                    if previous_period
                    else None
                ),
                delta=None,
                severity="CAUTION",
                description=(
                    f"Stockholders' equity is negative (-${abs(equity):,.0f}), reflecting accumulated retained losses or significant debt-funded share repurchases."
                ),
            )
        )

    return divergences
