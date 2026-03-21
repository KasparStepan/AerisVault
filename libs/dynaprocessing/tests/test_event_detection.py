"""Tests for event detection functions."""

import numpy as np
import pytest

from dynaprocessing.models.curve import Curve
from dynaprocessing.analysis.event_detection import (
    auto_detect_events,
    detect_deployment,
    detect_inflation_phases,
    detect_oscillations,
    detect_steady_state,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def deployment_curve():
    """Synthetic force profile: zero → ramp → peak → steady.

    Simulates a parachute deployment force signature.
    """
    t = np.linspace(0, 2, 2000)
    force = np.zeros_like(t)
    # Deployment ramp starting at t=0.5
    ramp_mask = (t >= 0.5) & (t < 1.0)
    force[ramp_mask] = 500 * (t[ramp_mask] - 0.5) / 0.5
    # Peak and decay
    peak_mask = t >= 1.0
    force[peak_mask] = 500 * np.exp(-3 * (t[peak_mask] - 1.0))
    # Add some noise
    np.random.seed(42)
    force += np.random.normal(0, 5, len(force))
    return Curve(time=t, values=force, name="Fpz", units="N")


@pytest.fixture
def steady_state_curve():
    """Signal that starts oscillating then converges to 100."""
    t = np.linspace(0, 5, 5000)
    v = 100.0 + 50.0 * np.exp(-2 * t) * np.sin(10 * t)
    return Curve(time=t, values=v, name="force")


@pytest.fixture
def oscillating_curve():
    """Pure oscillation at 5 Hz."""
    t = np.linspace(0, 2, 4000)  # fs = 2000 Hz
    v = 3.0 * np.sin(2 * np.pi * 5 * t)
    return Curve(time=t, values=v, name="osc")


# ---------------------------------------------------------------------------
# Deployment detection
# ---------------------------------------------------------------------------

class TestDeploymentDetection:
    def test_deployment_detected(self, deployment_curve):
        result = detect_deployment(deployment_curve, threshold_factor=0.1)
        assert result["detected"] is True
        # Deployment should be detected around t=0.5
        assert 0.3 < result["deployment_time"] < 0.8

    def test_zero_signal_no_deployment(self):
        t = np.linspace(0, 1, 100)
        v = np.zeros(100)
        c = Curve(time=t, values=v, name="zero")
        result = detect_deployment(c)
        assert result["detected"] is False


# ---------------------------------------------------------------------------
# Inflation phases
# ---------------------------------------------------------------------------

class TestInflationPhases:
    def test_inflation_detected(self, deployment_curve):
        result = detect_inflation_phases(deployment_curve)
        assert "start_time" in result
        assert "peak_time" in result
        assert "inflation_duration" in result
        assert result["inflation_duration"] > 0
        assert result["peak_force"] > 0


# ---------------------------------------------------------------------------
# Steady state detection
# ---------------------------------------------------------------------------

class TestSteadyStateDetection:
    def test_steady_state_detected(self, steady_state_curve):
        result = detect_steady_state(
            steady_state_curve, tolerance=0.05, window=50
        )
        assert result["detected"] is True
        assert result["steady_value"] == pytest.approx(100.0, abs=5.0)
        # Should reach steady state well before the end
        assert result["steady_time"] < 4.0

    def test_noisy_signal_not_steady(self):
        t = np.linspace(0, 1, 500)
        np.random.seed(0)
        v = np.random.randn(500) * 100
        c = Curve(time=t, values=v, name="noisy")
        result = detect_steady_state(c, tolerance=0.01, window=200)
        assert result["detected"] is False


# ---------------------------------------------------------------------------
# Oscillation detection
# ---------------------------------------------------------------------------

class TestOscillationDetection:
    def test_oscillation_detected(self, oscillating_curve):
        result = detect_oscillations(
            oscillating_curve, min_frequency=1.0, max_frequency=20.0
        )
        assert result["oscillating"] is True
        assert result["dominant_frequency"] == pytest.approx(5.0, abs=0.5)
        assert result["amplitude"] == pytest.approx(3.0, abs=0.5)


# ---------------------------------------------------------------------------
# Auto-detect
# ---------------------------------------------------------------------------

class TestAutoDetect:
    def test_auto_detect_returns_all_keys(self, deployment_curve):
        result = auto_detect_events(deployment_curve)
        assert "deployment" in result
        assert "inflation" in result
        assert "steady_state" in result
        assert "oscillations" in result
