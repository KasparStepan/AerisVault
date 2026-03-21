"""Tests for statistical analysis functions."""

import numpy as np
import pytest

from dynaprocessing.models.curve import Curve
from dynaprocessing.analysis.statistics import (
    basic_statistics,
    correlation_matrix,
    frequency_analysis,
    peak_detection,
    settling_time,
    time_window_statistics,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def constant_curve():
    """A constant signal for baseline tests."""
    t = np.linspace(0, 1, 500)
    v = np.full(500, 42.0)
    return Curve(time=t, values=v, name="const")


@pytest.fixture
def sine_curve():
    """A clean 10 Hz sine wave (fs = 1000 Hz)."""
    t = np.linspace(0, 1, 1000)
    v = np.sin(2 * np.pi * 10 * t)
    return Curve(time=t, values=v, name="sine_10hz")


@pytest.fixture
def settling_curve():
    """A signal that starts with transient then settles at 5.0."""
    t = np.linspace(0, 2, 2000)
    v = 5.0 + 10.0 * np.exp(-5 * t) * np.sin(20 * t)
    return Curve(time=t, values=v, name="settling_signal")


# ---------------------------------------------------------------------------
# Basic statistics
# ---------------------------------------------------------------------------

class TestBasicStatistics:
    def test_constant_signal(self, constant_curve):
        stats = basic_statistics(constant_curve)
        assert stats["mean"] == pytest.approx(42.0)
        assert stats["std"] == pytest.approx(0.0, abs=1e-10)
        assert stats["min"] == pytest.approx(42.0)
        assert stats["max"] == pytest.approx(42.0)
        assert stats["rms"] == pytest.approx(42.0)
        assert stats["median"] == pytest.approx(42.0)

    def test_sine_signal(self, sine_curve):
        stats = basic_statistics(sine_curve)
        assert stats["mean"] == pytest.approx(0.0, abs=0.01)
        assert stats["rms"] == pytest.approx(1.0 / np.sqrt(2), abs=0.02)

    def test_curve_convenience(self, sine_curve):
        """Curve.statistics() should produce identical results."""
        direct = basic_statistics(sine_curve)
        via_method = sine_curve.statistics()
        for key in direct:
            assert direct[key] == pytest.approx(via_method[key])


# ---------------------------------------------------------------------------
# Peak detection
# ---------------------------------------------------------------------------

class TestPeakDetection:
    def test_sine_peaks(self, sine_curve):
        result = peak_detection(sine_curve, prominence=0.05, distance=50)
        # A 10 Hz sine over 1 s should have ~10 peaks
        assert result["num_peaks"] >= 8
        assert result["num_peaks"] <= 12

    def test_constant_no_peaks(self, constant_curve):
        result = peak_detection(constant_curve)
        assert result["num_peaks"] == 0


# ---------------------------------------------------------------------------
# Settling time
# ---------------------------------------------------------------------------

class TestSettlingTime:
    def test_exponential_settling(self, settling_curve):
        result = settling_time(settling_curve, tolerance=0.05)
        assert result["settled"] is True
        # Should settle well before t = 2.0
        assert result["settling_time"] < 1.5
        assert result["settling_value"] == pytest.approx(5.0, abs=0.5)

    def test_constant_settles_immediately(self, constant_curve):
        result = settling_time(constant_curve, tolerance=0.05)
        assert result["settled"] is True
        assert result["settling_time"] == pytest.approx(0.0, abs=0.01)


# ---------------------------------------------------------------------------
# Frequency analysis
# ---------------------------------------------------------------------------

class TestFrequencyAnalysis:
    def test_dominant_frequency(self, sine_curve):
        result = frequency_analysis(sine_curve, num_frequencies=3)
        assert result["sampling_frequency"] == pytest.approx(1000.0, rel=0.01)
        # The dominant frequency should be ~10 Hz
        assert abs(result["dominant_frequencies"][0] - 10.0) < 1.0

    def test_constant_no_dominant_freq(self, constant_curve):
        result = frequency_analysis(constant_curve)
        # After DC removal, there should be no significant frequencies
        for mag in result["dominant_magnitudes"]:
            assert mag < 1.0


# ---------------------------------------------------------------------------
# Time window statistics
# ---------------------------------------------------------------------------

class TestTimeWindowStatistics:
    def test_windowed_stats(self, sine_curve):
        stats = time_window_statistics(sine_curve, 0.2, 0.8)
        assert "mean" in stats
        assert "rms" in stats

    def test_empty_window_raises(self, sine_curve):
        with pytest.raises(ValueError, match="No data points"):
            time_window_statistics(sine_curve, 10.0, 20.0)


# ---------------------------------------------------------------------------
# Correlation matrix
# ---------------------------------------------------------------------------

class TestCorrelationMatrix:
    def test_perfect_correlation(self):
        t = np.linspace(0, 1, 100)
        c1 = Curve(time=t, values=t, name="a")
        c2 = Curve(time=t, values=2 * t, name="b")
        mat = correlation_matrix([c1, c2])
        np.testing.assert_allclose(mat[0, 1], 1.0, atol=1e-10)

    def test_anticorrelation(self):
        t = np.linspace(0, 1, 100)
        c1 = Curve(time=t, values=t, name="a")
        c2 = Curve(time=t, values=-t, name="b")
        mat = correlation_matrix([c1, c2])
        np.testing.assert_allclose(mat[0, 1], -1.0, atol=1e-10)

    def test_mismatched_lengths_raises(self):
        c1 = Curve(time=np.array([0, 1]), values=np.array([1, 2]))
        c2 = Curve(time=np.array([0, 1, 2]), values=np.array([1, 2, 3]))
        with pytest.raises(ValueError, match="same number"):
            correlation_matrix([c1, c2])
