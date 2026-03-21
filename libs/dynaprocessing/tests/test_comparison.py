"""Tests for comparison utilities."""

import numpy as np
import pytest

from dynaprocessing.models.curve import Curve
from dynaprocessing.analysis.comparison import (
    align_curves,
    calculate_difference,
    calculate_rmse,
    compare_statistics,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def curve_a():
    """Curve with 100 points, 0..1 s."""
    t = np.linspace(0, 1, 100)
    v = np.sin(2 * np.pi * 5 * t)
    return Curve(time=t, values=v, name="signal_a")


@pytest.fixture
def curve_b():
    """Curve with 200 points, 0..1 s (same function, higher res)."""
    t = np.linspace(0, 1, 200)
    v = np.sin(2 * np.pi * 5 * t)
    return Curve(time=t, values=v, name="signal_b")


@pytest.fixture
def curve_offset():
    """Same as curve_a but shifted by +2.0."""
    t = np.linspace(0, 1, 100)
    v = np.sin(2 * np.pi * 5 * t) + 2.0
    return Curve(time=t, values=v, name="signal_offset")


# ---------------------------------------------------------------------------
# Alignment
# ---------------------------------------------------------------------------

class TestAlignCurves:
    def test_aligned_curves_same_length(self, curve_a, curve_b):
        aligned = align_curves([curve_a, curve_b])
        assert len(aligned[0]) == len(aligned[1])

    def test_aligned_time_arrays_equal(self, curve_a, curve_b):
        aligned = align_curves([curve_a, curve_b])
        np.testing.assert_array_equal(aligned[0].time, aligned[1].time)

    def test_single_curve_raises(self, curve_a):
        with pytest.raises(ValueError, match="at least 2"):
            align_curves([curve_a])

    def test_non_overlapping_raises(self):
        c1 = Curve(time=np.array([0, 1, 2]), values=np.array([1, 2, 3]))
        c2 = Curve(time=np.array([5, 6, 7]), values=np.array([1, 2, 3]))
        with pytest.raises(ValueError, match="No overlapping"):
            align_curves([c1, c2])

    def test_preserves_metadata(self, curve_a, curve_b):
        aligned = align_curves([curve_a, curve_b])
        assert aligned[0].name == "signal_a"
        assert aligned[1].name == "signal_b"


# ---------------------------------------------------------------------------
# RMSE
# ---------------------------------------------------------------------------

class TestRMSE:
    def test_identical_curves_zero_rmse(self, curve_a):
        rmse = calculate_rmse(curve_a, curve_a)
        assert rmse == pytest.approx(0.0, abs=1e-10)

    def test_known_offset_rmse(self, curve_a, curve_offset):
        rmse = calculate_rmse(curve_a, curve_offset)
        assert rmse == pytest.approx(2.0, abs=0.05)

    def test_different_resolution_works(self, curve_a, curve_b):
        # Same function, different resolution — RMSE should be near 0
        rmse = calculate_rmse(curve_a, curve_b)
        assert rmse < 0.1


# ---------------------------------------------------------------------------
# Difference
# ---------------------------------------------------------------------------

class TestDifference:
    def test_difference_values(self, curve_a, curve_offset):
        diff = calculate_difference(curve_a, curve_offset)
        # Difference should be approximately +2.0 everywhere
        np.testing.assert_allclose(diff.values, 2.0, atol=0.01)

    def test_difference_name(self, curve_a, curve_offset):
        diff = calculate_difference(curve_a, curve_offset)
        assert "diff" in diff.name


# ---------------------------------------------------------------------------
# Compare statistics
# ---------------------------------------------------------------------------

class TestCompareStatistics:
    def test_compare_returns_dataframe(self, curve_a, curve_offset):
        df = compare_statistics([curve_a, curve_offset])
        assert "mean" in df.columns
        assert "rms" in df.columns
        assert len(df) == 2

    def test_custom_labels(self, curve_a, curve_offset):
        df = compare_statistics(
            [curve_a, curve_offset], labels=["Sim1", "Sim2"]
        )
        assert "Sim1" in df.index
        assert "Sim2" in df.index
