import numpy as np
import pytest

from aerocfd.models.polar import Polar


class TestPolarConstruction:
    def test_construct_with_arrays(self, alpha_grid_deg):
        values = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        polar = Polar(alpha_deg=alpha_grid_deg, values=values, name="CL", units="-")
        assert polar.name == "CL"
        assert polar.units == "-"

    def test_alpha_and_values_are_arrays(self, alpha_grid_deg):
        polar = Polar(alpha_deg=alpha_grid_deg, values=np.zeros(5), name="dummy")
        assert isinstance(polar.alpha_deg, np.ndarray)
        assert isinstance(polar.values, np.ndarray)
        assert polar.alpha_deg.shape == polar.values.shape

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            Polar(alpha_deg=np.array([0.0, 5.0]), values=np.array([1.0]), name="bad")


class TestPolarInterpolation:
    def test_interpolate_at_known_point(self, alpha_grid_deg):
        # values increase linearly from 0 to 1 across α=-5..15
        values = np.linspace(0.0, 1.0, 5)
        polar = Polar(alpha_deg=alpha_grid_deg, values=values, name="linear")
        # midpoint α=5 must be 0.5 (the center of a 5-point linear ramp)
        assert polar.interpolate_at(5.0) == pytest.approx(0.5)

    def test_interpolate_outside_range_clips(self, alpha_grid_deg):
        # numpy.interp clips at the edges (no extrapolation). Lock that behavior.
        values = np.linspace(0.0, 1.0, 5)
        polar = Polar(alpha_deg=alpha_grid_deg, values=values, name="linear")
        assert polar.interpolate_at(-100.0) == pytest.approx(0.0)   # below alpha range
        assert polar.interpolate_at(100.0) == pytest.approx(1.0)    # above alpha range


class TestPolarSlicing:
    def test_slice_alpha_returns_subset(self, alpha_grid_deg):
        values = np.linspace(0.0, 1.0, 5)
        polar = Polar(alpha_deg=alpha_grid_deg, values=values, name="x")
        sub = polar.slice_alpha(0.0, 10.0)
        assert sub.alpha_deg.tolist() == [0.0, 5.0, 10.0]
        assert sub.values.tolist() == pytest.approx([0.25, 0.5, 0.75])
