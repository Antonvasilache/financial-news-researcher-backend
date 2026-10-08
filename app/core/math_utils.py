import math
from typing import Any


def safe_float(numeric_value: Any, default_value: float = 0.0) -> float:
    """Safely cast numeric value to finite float."""
    if numeric_value is None:
        return default_value
    try:
        float_value = float(numeric_value)
        return float_value if math.isfinite(float_value) else default_value
    except (ValueError, TypeError):
        return default_value


def safe_divide(
    numerator: float | None,
    denominator: float | None,
    decimal_places: int = 4,
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


def format_percentage(numeric_value: float | None) -> str:
    """Format floating point fraction as human-readable percentage string (e.g. '+15.2%')."""
    if numeric_value is None or not math.isfinite(numeric_value):
        return "N/A"
    prefix = "+" if numeric_value > 0 else ""
    return f"{prefix}{numeric_value * 100:.1f}%"


def format_ratio(numeric_value: float | None) -> str:
    """Format numeric ratio as human-readable multiple string (e.g. '2.40x')."""
    if numeric_value is None or not math.isfinite(numeric_value):
        return "N/A"
    return f"{numeric_value:.2f}x"
