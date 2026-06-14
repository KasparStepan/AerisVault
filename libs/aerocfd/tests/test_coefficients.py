import numpy as np
import pytest

from aerocfd.analysis.coefficients import (
    dynamic_pressure, cl, cd, cm, lift_to_drag,
)


class TestDynamicPressure:
    def test_known_value(self):
        # q = 0.5 · 1.225 · 50² = 1531.25 Pa
        assert dynamic_pressure(1.225, 50.0) == pytest.approx(1531.25)

    def test_array_velocity(self):
        v = np.array([10.0, 50.0, 100.0])
        q = dynamic_pressure(1.225, v)
        assert np.allclose(q, 0.5 * 1.225 * v**2)


class TestCoefficients:
    def test_cl_known_value(self):
        # CL = lift / (q · S_ref) = 1000 / (1531.25 · 10) = 0.0653...
        assert cl(1000.0, 1531.25, 10.0) == pytest.approx(1000.0 / 15312.5)

    def test_cd_known_value(self):
        assert cd(100.0, 1531.25, 10.0) == pytest.approx(100.0 / 15312.5)

    def test_cm_known_value(self):
        # Cm = My_aero / (q · S_ref · c_ref)
        assert cm(50.0, 1531.25, 10.0, 1.5) == pytest.approx(50.0 / (1531.25 * 10.0 * 1.5))


class TestLiftToDrag:
    def test_simple_ratio(self):
        assert lift_to_drag(1000.0, 100.0) == pytest.approx(10.0)

    def test_zero_drag_returns_inf(self):
        result = lift_to_drag(1000.0, 0.0)
        assert np.isinf(result)

    def test_array_input(self):
        lift = np.array([1000.0, 1000.0])
        drag = np.array([100.0, 200.0])
        assert np.allclose(lift_to_drag(lift, drag), [10.0, 5.0])
