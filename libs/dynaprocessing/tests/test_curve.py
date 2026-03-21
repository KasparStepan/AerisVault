"""Tests for the Curve class — the core data container."""

import numpy as np
import pytest

from dynaprocessing.models.curve import Curve, STANDARD_GRAVITY


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_curve():
    """A basic sine-wave curve for testing."""
    t = np.linspace(0, 1, 1000)
    v = np.sin(2 * np.pi * 10 * t)  # 10 Hz sine
    return Curve(time=t, values=v, name="test_signal", node_id="100", units="m/s^2")


@pytest.fixture
def force_curve():
    """A constant-force curve for drag coefficient tests."""
    t = np.linspace(0, 1, 100)
    v = np.full(100, 1000.0)  # 1000 N constant
    return Curve(time=t, values=v, name="Fpz", node_id=None, units="N")


# ---------------------------------------------------------------------------
# Construction & Validation
# ---------------------------------------------------------------------------

class TestCurveConstruction:
    def test_basic_creation(self, simple_curve):
        assert len(simple_curve) == 1000
        assert simple_curve.name == "test_signal"
        assert simple_curve.node_id == "100"
        assert simple_curve.units == "m/s^2"

    def test_arrays_are_readonly(self, simple_curve):
        with pytest.raises(ValueError):
            simple_curve.time[0] = 999.0
        with pytest.raises(ValueError):
            simple_curve.values[0] = 999.0

    def test_rejects_empty_arrays(self):
        with pytest.raises(ValueError, match="must not be empty"):
            Curve(time=np.array([]), values=np.array([]))

    def test_rejects_mismatched_lengths(self):
        with pytest.raises(ValueError, match="Length mismatch"):
            Curve(time=np.array([1, 2, 3]), values=np.array([1, 2]))

    def test_rejects_non_numeric(self):
        with pytest.raises(TypeError, match="must be numeric"):
            Curve(time=["a", "b"], values=[1, 2])

    def test_rejects_2d_arrays(self):
        with pytest.raises(ValueError, match="must be 1-D"):
            Curve(time=np.ones((2, 3)), values=np.ones((2, 3)))

    def test_accepts_lists(self):
        """Plain Python lists should be auto-converted to numpy arrays."""
        c = Curve(time=[0.0, 0.1, 0.2], values=[1.0, 2.0, 3.0])
        assert len(c) == 3
        assert isinstance(c.time, np.ndarray)

    def test_filter_history_default_empty(self, simple_curve):
        assert simple_curve.filter_history == []


# ---------------------------------------------------------------------------
# Immutability: all operations return NEW Curves
# ---------------------------------------------------------------------------

class TestCurveImmutability:
    def test_cfc_filter_returns_new(self, simple_curve):
        filtered = simple_curve.apply_cfc_filter(cfc=60)
        assert filtered is not simple_curve
        assert simple_curve.filter_history == []
        assert "CFC-60" in filtered.filter_history

    def test_butterworth_returns_new(self, simple_curve):
        filtered = simple_curve.apply_butterworth_filter(cutoff_freq=50)
        assert filtered is not simple_curve
        assert simple_curve.filter_history == []

    def test_moving_average_returns_new(self, simple_curve):
        filtered = simple_curve.apply_moving_average_filter(window_size=10)
        assert filtered is not simple_curve
        assert simple_curve.filter_history == []

    def test_to_g_returns_new(self, simple_curve):
        converted = simple_curve.to_g()
        assert converted is not simple_curve
        assert converted.units == "G"
        assert simple_curve.units == "m/s^2"  # original unchanged

    def test_chaining_preserves_original(self, simple_curve):
        result = simple_curve.apply_cfc_filter(60).to_g()
        assert len(result.filter_history) == 2
        assert simple_curve.filter_history == []  # still untouched


# ---------------------------------------------------------------------------
# Filtering correctness
# ---------------------------------------------------------------------------

class TestCurveFiltering:
    def test_cfc_filter_changes_values(self, simple_curve):
        """CFC filter should modify the signal (not return identical data)."""
        filtered = simple_curve.apply_cfc_filter(cfc=60)
        # The filtered signal should differ from the original
        assert not np.allclose(filtered.values, simple_curve.values)

    def test_butterworth_filter_changes_values(self, simple_curve):
        """Butterworth filter should modify the signal."""
        filtered = simple_curve.apply_butterworth_filter(cutoff_freq=50)
        assert not np.allclose(filtered.values, simple_curve.values)

    def test_moving_average_reduces_variance(self, simple_curve):
        """Moving average should reduce signal variance."""
        filtered = simple_curve.apply_moving_average_filter(window_size=20)
        assert np.std(filtered.values) < np.std(simple_curve.values)

    def test_filter_preserves_length(self, simple_curve):
        for method_name in ["apply_cfc_filter", "apply_moving_average_filter"]:
            filtered = getattr(simple_curve, method_name)()
            assert len(filtered) == len(simple_curve)


# ---------------------------------------------------------------------------
# Unit conversion
# ---------------------------------------------------------------------------

class TestUnitConversion:
    def test_to_g_values(self):
        t = np.array([0.0, 1.0])
        v = np.array([STANDARD_GRAVITY, 2 * STANDARD_GRAVITY])
        c = Curve(time=t, values=v, name="acc", units="m/s^2")
        converted = c.to_g()
        np.testing.assert_allclose(converted.values, [1.0, 2.0], atol=1e-10)
        assert converted.units == "G"

    def test_double_to_g_gives_correct_result(self):
        """Since Curve is immutable, calling to_g twice on the same
        original should give the same result."""
        t = np.array([0.0, 1.0])
        v = np.array([STANDARD_GRAVITY, 2 * STANDARD_GRAVITY])
        c = Curve(time=t, values=v, name="acc", units="m/s^2")
        first = c.to_g()
        second = c.to_g()
        np.testing.assert_array_equal(first.values, second.values)


# ---------------------------------------------------------------------------
# Drag coefficient
# ---------------------------------------------------------------------------

class TestDragCoefficient:
    def test_drag_coefficient_values(self, force_curve):
        cd = force_curve.calculate_drag_coefficient(v=10.0, A=1.0, rho=1.225)
        expected = 2.0 * 1000.0 / (1.225 * 100.0 * 1.0)
        np.testing.assert_allclose(cd.values, expected, atol=1e-10)
        assert cd.units == "dimensionless"
        assert "_Cd" in cd.name

    def test_drag_coefficient_rejects_zero_velocity(self, force_curve):
        with pytest.raises(ValueError, match="must be > 0"):
            force_curve.calculate_drag_coefficient(v=0, A=1.0)

    def test_drag_coefficient_rejects_zero_area(self, force_curve):
        with pytest.raises(ValueError, match="must be > 0"):
            force_curve.calculate_drag_coefficient(v=10.0, A=0)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class TestStatistics:
    def test_get_max(self):
        t = np.array([0.0, 1.0, 2.0])
        v = np.array([5.0, 10.0, 3.0])
        c = Curve(time=t, values=v)
        max_val, max_time = c.get_max()
        assert max_val == 10.0
        assert max_time == 1.0

    def test_get_min(self):
        t = np.array([0.0, 1.0, 2.0])
        v = np.array([5.0, 10.0, 3.0])
        c = Curve(time=t, values=v)
        min_val, min_time = c.get_min()
        assert min_val == 3.0
        assert min_time == 2.0


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

class TestExport:
    def test_to_dataframe(self, simple_curve):
        df = simple_curve.to_dataframe()
        assert list(df.columns) == ["time", "test_signal"]
        assert len(df) == 1000

    def test_to_parquet(self, simple_curve, tmp_path):
        out = simple_curve.to_parquet(tmp_path / "test.parquet")
        assert out.exists()
        import pandas as pd
        df = pd.read_parquet(out)
        assert len(df) == 1000
        assert "test_signal" in df.columns


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------

class TestRepr:
    def test_repr_basic(self, simple_curve):
        r = repr(simple_curve)
        assert "test_signal" in r
        assert "1000" in r

    def test_repr_with_filters(self, simple_curve):
        filtered = simple_curve.apply_cfc_filter(60)
        r = repr(filtered)
        assert "CFC-60" in r
