from pydantic import BaseModel, Field


class FinancialStatementMetrics(BaseModel):
    """Raw financial statement quantitative values in USD."""

    revenue: float | None = Field(None, description="Total revenue or net sales in USD")
    cost_of_revenue: float | None = Field(None, description="Cost of goods sold / revenue in USD")
    gross_profit: float | None = Field(None, description="Gross profit in USD")
    operating_income: float | None = Field(None, description="Operating income / EBIT in USD")
    net_income: float | None = Field(None, description="Net income or net loss in USD")
    operating_cash_flow: float | None = Field(
        None, description="Cash generated from operating activities in USD"
    )
    current_assets: float | None = Field(None, description="Total current assets in USD")
    total_assets: float | None = Field(None, description="Total assets in USD")
    current_liabilities: float | None = Field(
        None, description="Total current liabilities in USD"
    )
    total_liabilities: float | None = Field(None, description="Total liabilities in USD")
    stockholders_equity: float | None = Field(
        None, description="Total stockholders' equity in USD"
    )
    cash_and_equivalents: float | None = Field(
        None, description="Cash and cash equivalents in USD"
    )
    total_debt: float | None = Field(
        None, description="Total long-term and short-term debt in USD"
    )
    eps: float | None = Field(None, description="Earnings per share (diluted or basic) in USD")


class FinancialRatios(BaseModel):
    """Computed financial ratios, margins, and performance metrics."""

    gross_margin: float | None = Field(
        None, description="Gross margin ratio (Gross Profit / Revenue)"
    )
    operating_margin: float | None = Field(
        None, description="Operating margin ratio (Operating Income / Revenue)"
    )
    net_margin: float | None = Field(
        None, description="Net profit margin ratio (Net Income / Revenue)"
    )
    current_ratio: float | None = Field(
        None, description="Current liquidity ratio (Current Assets / Current Liabilities)"
    )
    debt_to_equity: float | None = Field(
        None, description="Solvency leverage ratio (Total Debt / Stockholders' Equity)"
    )
    debt_to_assets: float | None = Field(
        None, description="Debt to total assets ratio (Total Debt / Total Assets)"
    )
    return_on_equity: float | None = Field(
        None, description="Return on equity ratio (Net Income / Stockholders' Equity)"
    )
    return_on_assets: float | None = Field(
        None, description="Return on assets ratio (Net Income / Total Assets)"
    )
    revenue_growth_yoy: float | None = Field(
        None, description="Year-over-year revenue growth rate (percentage change)"
    )
    net_income_growth_yoy: float | None = Field(
        None, description="Year-over-year net income growth rate (percentage change)"
    )


class PeriodFinancials(BaseModel):
    """Structured financial figures and computed ratios for a specific period."""

    period: str = Field(..., description="Standardized period label, e.g. FY2024 or 2024-Q3")
    fiscal_year: int = Field(..., description="Fiscal year (e.g. 2024)")
    fiscal_period: str = Field(..., description="Fiscal period code (FY, Q1, Q2, Q3)")
    end_date: str = Field(..., description="Reporting period end date (YYYY-MM-DD)")
    filed_date: str | None = Field(None, description="Filing submission date (YYYY-MM-DD)")
    form: str = Field(..., description="Filing form type (10-K or 10-Q)")
    metrics: FinancialStatementMetrics = Field(
        ..., description="Raw financial statement items"
    )
    ratios: FinancialRatios = Field(
        ..., description="Computed financial ratios and profitability margins"
    )


class CompanyFinancialsResponse(BaseModel):
    """Aggregated financial statements and quantitative ratios for a tracked company."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g. AAPL)")
    cik: str = Field(..., description="10-digit SEC Central Index Key")
    company_name: str = Field(..., description="Registered company name")
    annual_reports: list[PeriodFinancials] = Field(
        default_factory=list,
        description="Historical annual periods from 10-K filings, ordered newest first",
    )
    quarterly_reports: list[PeriodFinancials] = Field(
        default_factory=list,
        description="Recent quarterly periods from 10-Q filings, ordered newest first",
    )
