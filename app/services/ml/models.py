import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier

from app.schemas.ml import FinancialTrendCategory
from app.services.ml.features import FEATURE_NAMES

ORDERED_CATEGORIES: list[FinancialTrendCategory] = [
    FinancialTrendCategory.ACCELERATING_GROWTH,
    FinancialTrendCategory.STABLE_COMPOUNDER,
    FinancialTrendCategory.MARGIN_COMPRESSION,
    FinancialTrendCategory.HIGH_FINANCIAL_STRESS,
]


class MLModelManager:
    """Manages training calibration and inference for Isolation Forest and Random Forest classifiers."""

    def __init__(self) -> None:
        self.classifier: RandomForestClassifier
        self.isolation_forest: IsolationForest
        self.decision_threshold: float = 0.60
        self._initialize_and_fit_models()

    def _initialize_and_fit_models(self) -> None:
        """Fit reference models on calibrated corporate financial baseline distributions."""
        random_generator = np.random.RandomState(42)

        def generate_samples(
            mean_vector: list[float], std_vector: list[float], sample_count: int
        ) -> np.ndarray:
            return random_generator.normal(
                loc=mean_vector, scale=std_vector, size=(sample_count, len(mean_vector))
            )

        # Class 0: ACCELERATING_GROWTH
        growth_samples = generate_samples(
            [0.28, 0.25, 0.55, 0.18, 2.2, 0.6, 0.03, 0.02, -0.05, 1.3, 0.30],
            [0.05, 0.04, 0.05, 0.03, 0.3, 0.2, 0.01, 0.01, 0.03, 0.2, 0.05],
            60,
        )
        # Class 1: STABLE_COMPOUNDER
        stable_samples = generate_samples(
            [0.07, 0.16, 0.42, 0.11, 1.7, 0.9, 0.00, 0.00, 0.00, 1.1, 0.18],
            [0.02, 0.02, 0.03, 0.02, 0.2, 0.2, 0.008, 0.008, 0.02, 0.1, 0.03],
            60,
        )
        # Class 2: MARGIN_COMPRESSION
        compression_samples = generate_samples(
            [0.06, 0.06, 0.26, 0.03, 1.3, 1.8, -0.06, -0.05, 0.15, 0.6, 0.06],
            [0.03, 0.02, 0.03, 0.02, 0.2, 0.3, 0.015, 0.015, 0.04, 0.15, 0.02],
            60,
        )
        # Class 3: HIGH_FINANCIAL_STRESS
        stress_samples = generate_samples(
            [-0.12, -0.10, 0.12, -0.15, 0.7, 4.5, -0.08, -0.06, 0.35, -0.4, -0.15],
            [0.05, 0.05, 0.04, 0.05, 0.15, 0.8, 0.02, 0.02, 0.08, 0.3, 0.05],
            60,
        )

        training_features = np.vstack(
            [growth_samples, stable_samples, compression_samples, stress_samples]
        )
        training_labels = np.array([0] * 60 + [1] * 60 + [2] * 60 + [3] * 60)

        # Train Random Forest Classifier for trend classification
        self.classifier = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        self.classifier.fit(training_features, training_labels)

        # Train Isolation Forest on composite baseline distributions
        self.isolation_forest = IsolationForest(
            n_estimators=100, contamination=0.12, random_state=42
        )
        self.isolation_forest.fit(training_features)

    def to_feature_array(self, feature_vector_map: dict[str, float]) -> np.ndarray:
        """Convert feature dictionary into a 2D numpy array suitable for scikit-learn models."""
        return np.array([[feature_vector_map[name] for name in FEATURE_NAMES]])

    def score_anomaly(self, feature_vector_map: dict[str, float]) -> tuple[float, float]:
        """Compute Isolation Forest statistical anomaly scores (raw and normalized)."""
        feature_array = self.to_feature_array(feature_vector_map)
        raw_isolation_score = float(self.isolation_forest.decision_function(feature_array)[0])
        normalized_anomaly_score = float(
            np.clip((0.15 - raw_isolation_score) / 0.35, 0.0, 1.0)
        )
        return round(raw_isolation_score, 4), round(normalized_anomaly_score, 4)

    def classify_trend(
        self, feature_vector_map: dict[str, float]
    ) -> tuple[FinancialTrendCategory, float]:
        """Classify financial trend category and associated probability confidence."""
        feature_array = self.to_feature_array(feature_vector_map)
        class_probabilities = self.classifier.predict_proba(feature_array)[0]
        predicted_index = int(np.argmax(class_probabilities))
        category = ORDERED_CATEGORIES[predicted_index]
        confidence = round(float(class_probabilities[predicted_index]), 4)
        return category, confidence
