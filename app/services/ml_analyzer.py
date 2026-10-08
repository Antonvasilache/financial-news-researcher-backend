from app.schemas.financials import CompanyFinancialsResponse, PeriodFinancials
from app.schemas.ml import (
    AnomalyDetectionResult,
    AnomalyDivergence,
    AnomalySeverity,
    CompanyFinancialAnalysisResponse,
    FeatureImpact,
    FinancialTrendCategory,
    FinancialTrendResult,
    PeriodSummaryItem,
)
from app.services.ml import (
    DEFAULT_FEATURE_VALUES,
    FEATURE_NAMES,
    ORDERED_CATEGORIES,
    TREND_LABELS,
    TREND_SUMMARIES,
    MLModelManager,
    detect_heuristic_divergences,
    extract_feature_vector,
    generate_key_drivers,
)

__all__ = [
    "DEFAULT_FEATURE_VALUES",
    "FEATURE_NAMES",
    "ORDERED_CATEGORIES",
    "TREND_LABELS",
    "TREND_SUMMARIES",
    "FinancialMLAnalyzerService",
]


class FinancialMLAnalyzerService:
    """Service providing machine learning anomaly detection and trend classification for company financials."""

    def __init__(self) -> None:
        self.model_manager = MLModelManager()
        self.classifier = self.model_manager.classifier
        self.isolation_forest = self.model_manager.isolation_forest
        self.decision_threshold: float = self.model_manager.decision_threshold

    def extract_feature_vector(
        self,
        current_period: PeriodFinancials,
        previous_period: PeriodFinancials | None,
    ) -> dict[str, float]:
        """Delegate feature vector extraction to the ml.features module."""
        return extract_feature_vector(
            current_period=current_period,
            previous_period=previous_period,
        )

    def detect_heuristic_divergences(
        self,
        current_period: PeriodFinancials,
        previous_period: PeriodFinancials | None,
        feature_vector: dict[str, float],
    ) -> list[AnomalyDivergence]:
        """Delegate heuristic red-flag divergence detection to the ml.rules module."""
        return detect_heuristic_divergences(
            current_period=current_period,
            previous_period=previous_period,
            feature_vector=feature_vector,
        )

    def generate_key_drivers(
        self,
        category: FinancialTrendCategory,
        feature_vector: dict[str, float],
    ) -> list[FeatureImpact]:
        """Delegate key driver generation to the ml.drivers module."""
        return generate_key_drivers(
            category=category,
            feature_vector=feature_vector,
        )

    def analyze_financials(
        self,
        financials: CompanyFinancialsResponse,
        period_type: str = "quarterly",
    ) -> CompanyFinancialAnalysisResponse:
        """Perform comprehensive ML anomaly detection and trend classification on company financials."""
        selected_reports: list[PeriodFinancials] = []
        effective_reporting_type = period_type.lower()

        if effective_reporting_type == "quarterly" and financials.quarterly_reports:
            selected_reports = financials.quarterly_reports
        elif effective_reporting_type == "annual" and financials.annual_reports:
            selected_reports = financials.annual_reports
        elif financials.quarterly_reports:
            selected_reports = financials.quarterly_reports
            effective_reporting_type = "quarterly"
        elif financials.annual_reports:
            selected_reports = financials.annual_reports
            effective_reporting_type = "annual"

        # Edge case: No financial reports available
        if not selected_reports:
            return CompanyFinancialAnalysisResponse(
                ticker=financials.ticker,
                cik=financials.cik,
                company_name=financials.company_name,
                analyzed_period="N/A",
                periods_analyzed_count=0,
                reporting_type=effective_reporting_type,
                anomaly_detection=AnomalyDetectionResult(
                    status=AnomalySeverity.NORMAL,
                    is_anomaly=False,
                    anomaly_score=0.0,
                    decision_threshold=self.decision_threshold,
                    detected_divergences=[],
                    model_method="Isolation Forest (scikit-learn) + Heuristic Divergence",
                ),
                trend_classification=FinancialTrendResult(
                    category=FinancialTrendCategory.STABLE_COMPOUNDER,
                    label=TREND_LABELS[FinancialTrendCategory.STABLE_COMPOUNDER],
                    confidence=0.50,
                    summary="Insufficient reporting periods to model trend dynamics.",
                    key_drivers=[],
                ),
                historical_sequence=[],
            )

        # Order chronologically (oldest first, newest last) for delta computation
        chronological_reports = list(reversed(selected_reports))
        target_period = chronological_reports[-1]
        previous_period = (
            chronological_reports[-2] if len(chronological_reports) >= 2 else None
        )

        # 1. Feature Vector
        feature_vector_map = self.extract_feature_vector(
            current_period=target_period,
            previous_period=previous_period,
        )

        # 2. Isolation Forest Statistical Anomaly Score
        _raw_isolation_score, normalized_anomaly_score = self.model_manager.score_anomaly(
            feature_vector_map
        )

        # 3. Rule-augmented Heuristic Divergences
        detected_divergences = self.detect_heuristic_divergences(
            current_period=target_period,
            previous_period=previous_period,
            feature_vector=feature_vector_map,
        )

        # 4. Resolve Aggregate Anomaly Severity Status
        has_severe_divergence = any(
            divergence_item.severity == "SEVERE_ANOMALY"
            for divergence_item in detected_divergences
        )
        caution_count = sum(
            1
            for divergence_item in detected_divergences
            if divergence_item.severity == "CAUTION"
        )

        if (
            has_severe_divergence
            or caution_count >= 2
            or normalized_anomaly_score >= 0.70
        ):
            anomaly_status = AnomalySeverity.SEVERE_ANOMALY
            is_anomaly = True
        elif (
            len(detected_divergences) > 0
            or normalized_anomaly_score >= self.decision_threshold
        ):
            anomaly_status = AnomalySeverity.CAUTION
            is_anomaly = True
        else:
            anomaly_status = AnomalySeverity.NORMAL
            is_anomaly = False

        anomaly_result = AnomalyDetectionResult(
            status=anomaly_status,
            is_anomaly=is_anomaly,
            anomaly_score=normalized_anomaly_score,
            decision_threshold=self.decision_threshold,
            detected_divergences=detected_divergences,
            model_method="Isolation Forest (scikit-learn) + Heuristic Divergence",
        )

        # 5. Trend Classification via Random Forest
        trend_category, confidence = self.model_manager.classify_trend(feature_vector_map)

        key_drivers = self.generate_key_drivers(
            category=trend_category,
            feature_vector=feature_vector_map,
        )

        trend_result = FinancialTrendResult(
            category=trend_category,
            label=TREND_LABELS[trend_category],
            confidence=confidence,
            summary=TREND_SUMMARIES[trend_category],
            key_drivers=key_drivers,
        )

        # 6. Historical Sequence for UI Charts
        historical_sequence: list[PeriodSummaryItem] = []
        for period_record in chronological_reports:
            historical_sequence.append(
                PeriodSummaryItem(
                    period=period_record.period,
                    fiscal_year=period_record.fiscal_year,
                    fiscal_period=period_record.fiscal_period,
                    revenue=period_record.metrics.revenue,
                    operating_income=period_record.metrics.operating_income,
                    net_income=period_record.metrics.net_income,
                    operating_margin=period_record.ratios.operating_margin,
                    net_margin=period_record.ratios.net_margin,
                    current_ratio=period_record.ratios.current_ratio,
                    debt_to_equity=period_record.ratios.debt_to_equity,
                )
            )

        return CompanyFinancialAnalysisResponse(
            ticker=financials.ticker,
            cik=financials.cik,
            company_name=financials.company_name,
            analyzed_period=target_period.period,
            periods_analyzed_count=len(selected_reports),
            reporting_type=effective_reporting_type,
            anomaly_detection=anomaly_result,
            trend_classification=trend_result,
            historical_sequence=historical_sequence,
        )
