from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class AnomalySeverity(str, Enum):
    """Severity tier for detected financial anomalies."""

    NORMAL = "NORMAL"
    CAUTION = "CAUTION"
    SEVERE_ANOMALY = "SEVERE_ANOMALY"


class FinancialTrendCategory(str, Enum):
    """High-level financial trajectory category determined by ML classifier."""

    ACCELERATING_GROWTH = "ACCELERATING_GROWTH"
    STABLE_COMPOUNDER = "STABLE_COMPOUNDER"
    MARGIN_COMPRESSION = "MARGIN_COMPRESSION"
    HIGH_FINANCIAL_STRESS = "HIGH_FINANCIAL_STRESS"


class FeatureImpact(BaseModel):
    """Specific financial driver contributing to trend classification and valuation profile."""

    feature_name: str = Field(..., description="Machine-readable feature identifier")
    label: str = Field(..., description="Display title for the financial metric (e.g. Operating Margin)")
    current_value: float | None = Field(default=None, description="Observed numeric value of the metric")
    formatted_value: str = Field(
        ..., description="Human-readable formatted string, e.g. '+15.2%' or '2.4x'"
    )
    impact_direction: Literal["POSITIVE", "NEGATIVE", "NEUTRAL"] = Field(
        ..., description="Directional contribution to the company financial profile"
    )
    description: str = Field(..., description="Contextual interpretation of this metric in the analysis")


class AnomalyDivergence(BaseModel):
    """Specific statistical divergence or operational anomaly detected in financial disclosures."""

    metric_name: str = Field(..., description="Identifier of the divergent financial metric")
    metric_label: str = Field(..., description="Display title for the metric")
    current_value: float | None = Field(default=None, description="Observed value in the current period")
    previous_value: float | None = Field(default=None, description="Baseline or previous period value")
    delta: float | None = Field(default=None, description="Numerical divergence magnitude or difference")
    severity: Literal["CAUTION", "SEVERE_ANOMALY"] = Field(
        ..., description="Severity classification of the anomaly"
    )
    description: str = Field(..., description="Clear explanation of the detected divergence")


class AnomalyDetectionResult(BaseModel):
    """Statistical and heuristic anomaly detection results for the target reporting period."""

    status: AnomalySeverity = Field(
        ..., description="Aggregate anomaly severity badge (NORMAL, CAUTION, SEVERE_ANOMALY)"
    )
    is_anomaly: bool = Field(..., description="Whether a caution or severe anomaly was triggered")
    anomaly_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized anomaly score between 0.0 (baseline normality) and 1.0 (extreme outlier)",
    )
    decision_threshold: float = Field(
        ..., description="Threshold score above which statistical anomaly is flagged"
    )
    detected_divergences: list[AnomalyDivergence] = Field(
        default_factory=list, description="List of specific identified divergences and red flags"
    )
    model_method: str = Field(
        ..., description="Underlying detection methodology (e.g. Isolation Forest + Heuristics)"
    )


class FinancialTrendResult(BaseModel):
    """Machine learning classification of corporate financial trajectory and investment profile."""

    category: FinancialTrendCategory = Field(..., description="Categorical classification profile")
    label: str = Field(..., description="Human-readable profile title (e.g. Accelerating Growth)")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model probability confidence for this category"
    )
    summary: str = Field(..., description="Executive narrative explaining the trend trajectory")
    key_drivers: list[FeatureImpact] = Field(
        default_factory=list, description="Key metrics and ratio drivers influencing the classification"
    )


class PeriodSummaryItem(BaseModel):
    """Compact summary of key indicators for a historical period to support UI trend visualizations."""

    period: str = Field(..., description="Period identifier, e.g. 2024-Q3 or FY2024")
    fiscal_year: int = Field(..., description="Fiscal reporting year")
    fiscal_period: str = Field(..., description="Fiscal quarter or annual designation (Q1-Q4, FY)")
    revenue: float | None = Field(default=None, description="Revenue in USD")
    operating_income: float | None = Field(default=None, description="Operating income in USD")
    net_income: float | None = Field(default=None, description="Net income in USD")
    operating_margin: float | None = Field(default=None, description="Operating margin ratio")
    net_margin: float | None = Field(default=None, description="Net margin ratio")
    current_ratio: float | None = Field(default=None, description="Current liquidity ratio")
    debt_to_equity: float | None = Field(default=None, description="Solvency leverage ratio")


class CompanyFinancialAnalysisResponse(BaseModel):
    """Combined quantitative anomaly detection and machine learning trend analysis for a company."""

    ticker: str = Field(..., description="Company ticker symbol (e.g. AAPL)")
    cik: str = Field(..., description="SEC CIK identifier")
    company_name: str = Field(..., description="Company legal name")
    analyzed_period: str = Field(
        ..., description="Target reporting period evaluated (e.g. 2024-Q3 or FY2024)"
    )
    periods_analyzed_count: int = Field(
        ..., description="Total historical periods evaluated in the sequence"
    )
    reporting_type: str = Field(
        ..., description="Type of reports evaluated ('quarterly' or 'annual')"
    )
    anomaly_detection: AnomalyDetectionResult = Field(
        ..., description="Anomaly detection evaluation and flagged divergences"
    )
    trend_classification: FinancialTrendResult = Field(
        ..., description="Machine learning trajectory profile and key drivers"
    )
    historical_sequence: list[PeriodSummaryItem] = Field(
        default_factory=list,
        description="Historical period metrics in chronological order (oldest to newest) for charts",
    )
