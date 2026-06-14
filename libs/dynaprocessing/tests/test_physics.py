"""Tests for Curve physics methods: to_force, calculate_cds, calculate_cds_from_velocity."""

import numpy as np
import pytest

from dynaprocessing.models.curve import Curve


@pytest.fixture
def acceleration_curve():
    """A constant 10 m/s² acceleration over 1 second (100 points)."""
    t = np.linspace(0, 1, 100)
    a = np.full(100, 10.0)  # 10 m/s²
    return Curve(time=t, values=a, name="z_acceleration", units="m/s^2")


@pytest.fixture
def force_curve():
    """A constant 100 N force over 1 second."""
    t = np.linspace(0, 1, 100)
    f = np.full(100, 100.0)
    return Curve(time=t, values=f, name="Fpz", units="N")


@pytest.fixture
def velocity_curve():
    """A velocity decreasing from 10 m/s to 5 m/s linearly."""
    t = np.linspace(0, 1, 100)
    v = np.linspace(10, 5, 100)
    return Curve(time=t, values=v, name="resultant_velocity", units="m/s")


class TestToForce:
    def test_force_equals_mass_times_acceleration(self, acceleration_curve):
        mass = 5.0  # kg
        force = acceleration_curve.to_force(mass)
        # F = 5 * 10 = 50 N
        np.testing.assert_allclose(force.values, 50.0)

    def test_force_units_are_newtons(self, acceleration_curve):
        force = acceleration_curve.to_force(5.0)
        assert force.units == "N"

    def test_force_name_reflects_source(self, acceleration_curve):
        force = acceleration_curve.to_force(5.0)
        assert "force" in force.name

    def test_force_preserves_time(self, acceleration_curve):
        force = acceleration_curve.to_force(5.0)
        np.testing.assert_array_equal(force.time, acceleration_curve.time)

    def test_force_returns_new_curve(self, acceleration_curve):
        force = acceleration_curve.to_force(5.0)
        assert force is not acceleration_curve

    def test_zero_mass_raises(self, acceleration_curve):
        with pytest.raises(ValueError, match="positive"):
            acceleration_curve.to_force(0)

    def test_negative_mass_raises(self, acceleration_curve):
        with pytest.raises(ValueError, match="positive"):
            acceleration_curve.to_force(-1.0)


class TestCalculateCdS:
    def test_known_cds_value(self, force_curve):
        # CdS = F / (0.5 * rho * v²)
        # F=100 N, rho=1.225, v=10 m/s → q = 0.5 * 1.225 * 100 = 61.25
        # CdS = 100 / 61.25 = 1.6327 m²
        cds = force_curve.calculate_cds(v=10.0, rho=1.225)
        expected = 100.0 / (0.5 * 1.225 * 100.0)
        np.testing.assert_allclose(cds.values, expected, rtol=1e-10)

    def test_cds_units_are_m_squared(self, force_curve):
        cds = force_curve.calculate_cds(v=10.0)
        assert cds.units == "m^2"

    def test_cds_zero_velocity_raises(self, force_curve):
        with pytest.raises(ValueError, match="non-zero"):
            force_curve.calculate_cds(v=0)

    def test_cds_filter_history_logged(self, force_curve):
        cds = force_curve.calculate_cds(v=10.0)
        assert len(cds.filter_history) == 1
        assert "CdS" in cds.filter_history[0]


class TestCalculateCdSFromVelocity:
    def test_variable_velocity_cds(self, force_curve, velocity_curve):
        cds = force_curve.calculate_cds_from_velocity(velocity_curve, rho=1.225)

        # At t=0: v=10 m/s → q=61.25 → CdS = 100/61.25 = 1.6327
        expected_start = 100.0 / (0.5 * 1.225 * 10.0**2)
        assert abs(cds.values[0] - expected_start) < 1e-6

        # At t=end: v=5 m/s → q=15.3125 → CdS = 100/15.3125 = 6.5306
        expected_end = 100.0 / (0.5 * 1.225 * 5.0**2)
        assert abs(cds.values[-1] - expected_end) < 1e-6

    def test_near_zero_velocity_gives_nan(self, force_curve):
        # Velocity that goes to zero
        t = np.linspace(0, 1, 100)
        v_with_zero = np.linspace(10, 0, 100)
        vel = Curve(time=t, values=v_with_zero, name="v")

        cds = force_curve.calculate_cds_from_velocity(vel)
        # Last values where v < 0.1 should be NaN
        assert np.isnan(cds.values[-1])
        # First values where v is high should be valid numbers
        assert not np.isnan(cds.values[0])

    def test_length_mismatch_raises(self, force_curve):
        short_vel = Curve(
            time=np.linspace(0, 1, 50),
            values=np.ones(50),
            name="v",
        )
        with pytest.raises(ValueError, match="must match"):
            force_curve.calculate_cds_from_velocity(short_vel)

    def test_cds_units_are_m_squared(self, force_curve, velocity_curve):
        cds = force_curve.calculate_cds_from_velocity(velocity_curve)
        assert cds.units == "m^2"

    def test_no_divide_by_zero_warning(self, force_curve):
        """Velocity reaching zero must not emit a RuntimeWarning."""
        import warnings

        t = np.linspace(0, 1, 100)
        v_to_zero = np.linspace(10, 0, 100)
        vel = Curve(time=t, values=v_to_zero, name="v")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            cds = force_curve.calculate_cds_from_velocity(vel)

        runtime_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
        assert not runtime_warnings, f"unexpected RuntimeWarning(s): {[str(w.message) for w in runtime_warnings]}"
        assert np.isnan(cds.values[-1])


class TestResultant:
    """Tests for Curve.resultant() — magnitude of component vectors."""

    @pytest.fixture
    def xyz_force_curves(self):
        """Three orthogonal force components: Fpx=3, Fpy=4, Fpz=0 → |F|=5."""
        t = np.linspace(0, 1, 100)
        fpx = Curve(time=t, values=np.full(100, 3.0), name="Fpx", units="N")
        fpy = Curve(time=t, values=np.full(100, 4.0), name="Fpy", units="N")
        fpz = Curve(time=t, values=np.full(100, 0.0), name="Fpz", units="N")
        return fpx, fpy, fpz

    def test_known_resultant_3_4_0(self, xyz_force_curves):
        fpx, fpy, fpz = xyz_force_curves
        result = Curve.resultant(fpx, fpy, fpz)
        # sqrt(3² + 4² + 0²) = 5
        np.testing.assert_allclose(result.values, 5.0)

    def test_resultant_name(self, xyz_force_curves):
        result = Curve.resultant(*xyz_force_curves)
        assert result.name == "resultant_force"

    def test_resultant_units_from_first_component(self, xyz_force_curves):
        result = Curve.resultant(*xyz_force_curves)
        assert result.units == "N"

    def test_resultant_preserves_time(self, xyz_force_curves):
        fpx, fpy, fpz = xyz_force_curves
        result = Curve.resultant(fpx, fpy, fpz)
        np.testing.assert_array_equal(result.time, fpx.time)

    def test_resultant_filter_history(self, xyz_force_curves):
        result = Curve.resultant(*xyz_force_curves)
        assert len(result.filter_history) == 1
        assert "resultant" in result.filter_history[0]

    def test_resultant_two_components(self):
        t = np.linspace(0, 1, 50)
        c1 = Curve(time=t, values=np.full(50, 3.0), name="Fx", units="N")
        c2 = Curve(time=t, values=np.full(50, 4.0), name="Fy", units="N")
        result = Curve.resultant(c1, c2)
        np.testing.assert_allclose(result.values, 5.0)

    def test_single_component_raises(self):
        t = np.linspace(0, 1, 50)
        c1 = Curve(time=t, values=np.full(50, 3.0), name="Fx")
        with pytest.raises(ValueError, match="at least 2"):
            Curve.resultant(c1)

    def test_length_mismatch_raises(self):
        c1 = Curve(time=np.linspace(0, 1, 50), values=np.ones(50), name="Fx")
        c2 = Curve(time=np.linspace(0, 1, 100), values=np.ones(100), name="Fy")
        with pytest.raises(ValueError, match="same length"):
            Curve.resultant(c1, c2)
