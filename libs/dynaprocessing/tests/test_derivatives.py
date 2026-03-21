"""Tests for derivative calculations."""

import numpy as np
import pytest

from dynaprocessing.models.curve import Curve
from dynaprocessing.analysis.derivatives import first_derivative, second_derivative


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def linear_curve():
    """y = 3t  →  dy/dt = 3,  d²y/dt² = 0."""
    t = np.linspace(0, 1, 1000)
    v = 3.0 * t
    return Curve(time=t, values=v, name="linear")


@pytest.fixture
def quadratic_curve():
    """y = t²  →  dy/dt = 2t,  d²y/dt² = 2."""
    t = np.linspace(0, 1, 1000)
    v = t ** 2
    return Curve(time=t, values=v, name="quadratic")


@pytest.fixture
def sine_curve():
    """y = sin(2πt)  →  dy/dt = 2π·cos(2πt)."""
    t = np.linspace(0, 1, 5000)
    v = np.sin(2 * np.pi * t)
    return Curve(time=t, values=v, name="sine")


# ---------------------------------------------------------------------------
# First derivative
# ---------------------------------------------------------------------------

class TestFirstDerivative:
    def test_linear_derivative_is_constant(self, linear_curve):
        d = first_derivative(linear_curve)
        # d(3t)/dt = 3 — skip edges to avoid boundary effects
        n = len(d)
        interior = d.values[n // 10 : -n // 10]
        np.testing.assert_allclose(interior, 3.0, atol=0.01)

    def test_quadratic_derivative(self, quadratic_curve):
        d = first_derivative(quadratic_curve)
        # d(t²)/dt = 2t
        expected = 2.0 * quadratic_curve.time
        n = len(d)
        np.testing.assert_allclose(
            d.values[n // 10 : -n // 10],
            expected[n // 10 : -n // 10],
            atol=0.01,
        )

    def test_derivative_name(self, linear_curve):
        d = first_derivative(linear_curve)
        assert "dlinear_dt" in d.name

    def test_preserves_length(self, linear_curve):
        d = first_derivative(linear_curve)
        assert len(d) == len(linear_curve)

    def test_smooth_option(self, sine_curve):
        """Smoothed derivative should still be reasonable."""
        d = first_derivative(sine_curve, smooth=True, window=10)
        assert len(d) == len(sine_curve)


# ---------------------------------------------------------------------------
# Second derivative
# ---------------------------------------------------------------------------

class TestSecondDerivative:
    def test_quadratic_second_derivative(self, quadratic_curve):
        d2 = second_derivative(quadratic_curve)
        # d²(t²)/dt² = 2
        n = len(d2)
        interior = d2.values[n // 10 : -n // 10]
        np.testing.assert_allclose(interior, 2.0, atol=0.1)

    def test_linear_second_derivative_zero(self, linear_curve):
        d2 = second_derivative(linear_curve)
        # d²(3t)/dt² = 0
        n = len(d2)
        interior = d2.values[n // 10 : -n // 10]
        np.testing.assert_allclose(interior, 0.0, atol=0.1)


# ---------------------------------------------------------------------------
# Curve convenience method
# ---------------------------------------------------------------------------

class TestCurveDerivativeMethod:
    def test_derivative_method_order_1(self, linear_curve):
        d = linear_curve.derivative(order=1)
        n = len(d)
        interior = d.values[n // 10 : -n // 10]
        np.testing.assert_allclose(interior, 3.0, atol=0.01)

    def test_derivative_method_order_2(self, quadratic_curve):
        d2 = quadratic_curve.derivative(order=2)
        n = len(d2)
        interior = d2.values[n // 10 : -n // 10]
        np.testing.assert_allclose(interior, 2.0, atol=0.1)

    def test_invalid_order_raises(self, linear_curve):
        with pytest.raises(ValueError, match="Only order 1 or 2"):
            linear_curve.derivative(order=3)
