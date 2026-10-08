
from app.core.math_utils import (
    calculate_growth_rate,
    format_percentage,
    format_ratio,
    safe_divide,
    safe_float,
)


def test_safe_float():
    """Verify safe float conversion with diverse inputs, defaults, and non-finite values."""
    assert safe_float("123.45") == 123.45
    assert safe_float(42) == 42.0
    assert safe_float(-8.5) == -8.5
    assert safe_float(None, default_value=1.5) == 1.5
    assert safe_float("invalid_string", default_value=0.0) == 0.0
    assert safe_float(float("nan"), default_value=9.9) == 9.9
    assert safe_float(float("inf"), default_value=9.9) == 9.9
    assert safe_float(float("-inf"), default_value=-1.0) == -1.0


def test_safe_divide():
    """Verify division safety with zeroes, non-finite values, and precision rounding."""
    assert safe_divide(10.0, 2.0) == 5.0
    assert safe_divide(1.0, 3.0, decimal_places=4) == 0.3333
    assert safe_divide(10.0, 0.0) is None
    assert safe_divide(None, 5.0) is None
    assert safe_divide(5.0, None) is None
    assert safe_divide(float("nan"), 2.0) is None
    assert safe_divide(2.0, float("inf")) is None


def test_calculate_growth_rate():
    """Verify percentage growth calculations with negative and zero bases."""
    # Standard positive growth
    assert calculate_growth_rate(120.0, 100.0) == 0.20
    # Negative growth
    assert calculate_growth_rate(80.0, 100.0) == -0.20
    # Negative base to positive value
    assert calculate_growth_rate(50.0, -100.0) == 1.50
    # Zero base returns None
    assert calculate_growth_rate(100.0, 0.0) is None
    # None or non-finite inputs
    assert calculate_growth_rate(None, 100.0) is None
    assert calculate_growth_rate(100.0, None) is None
    assert calculate_growth_rate(float("nan"), 100.0) is None


def test_format_percentage():
    """Verify percentage string formatting with positive, negative, zero, and null values."""
    assert format_percentage(0.152) == "+15.2%"
    assert format_percentage(-0.045) == "-4.5%"
    assert format_percentage(0.0) == "0.0%"
    assert format_percentage(None) == "N/A"
    assert format_percentage(float("nan")) == "N/A"
    assert format_percentage(float("inf")) == "N/A"


def test_format_ratio():
    """Verify multiple/ratio string formatting with floats, zero, and null values."""
    assert format_ratio(2.4) == "2.40x"
    assert format_ratio(0.854) == "0.85x"
    assert format_ratio(0.0) == "0.00x"
    assert format_ratio(None) == "N/A"
    assert format_ratio(float("nan")) == "N/A"
    assert format_ratio(float("inf")) == "N/A"
