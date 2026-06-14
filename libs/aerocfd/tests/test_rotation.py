import numpy as np
import pytest

from aerocfd.analysis.rotation import body_to_wind, fluent_my_to_aero


class TestBodyToWindGoldStandards:
    """Rotation gold tests #1 and #2. If these ever fail, the convention is broken."""

    def test_zero_alpha_drag_lift(self):
        # Fluent Fx is forward-positive; drag points -X. At α=0 the body and
        # wind axes align, so drag = -Fx (positive for a draggy body, Fx<0)
        # and lift = +Fz. With Fx=-100 (a drag force of 100 N), drag = +100.
        drag, lift = body_to_wind(fx_n=-100.0, fz_n=1000.0, alpha_deg=0.0)
        assert drag == pytest.approx(100.0)
        assert lift == pytest.approx(1000.0)

    def test_pure_vertical_force_at_10_deg(self):
        # Pure +Fz of 1000 N at α=10°:
        # drag = 0·cos(10°) + 1000·sin(10°) = +173.6 N
        # lift = -0·sin(10°) + 1000·cos(10°) = +984.8 N
        drag, lift = body_to_wind(fx_n=0.0, fz_n=1000.0, alpha_deg=10.0)
        assert drag == pytest.approx(1000.0 * np.sin(np.radians(10.0)))
        assert lift == pytest.approx(1000.0 * np.cos(np.radians(10.0)))

    def test_array_broadcasting(self):
        fx = np.array([0.0, 0.0, 0.0])
        fz = np.array([1000.0, 1000.0, 1000.0])
        alpha = np.array([0.0, 10.0, 20.0])
        drag, lift = body_to_wind(fx, fz, alpha)
        assert drag.shape == (3,)
        assert lift.shape == (3,)
        assert drag[0] == pytest.approx(0.0)
        assert lift[0] == pytest.approx(1000.0)


class TestFluentMyToAero:
    def test_sign_is_flipped(self):
        # Fluent's right-hand-rule My, with y pointing left, is nose-DOWN positive.
        # Aerospace Cm is nose-UP positive. So the conversion is a sign flip.
        assert fluent_my_to_aero(50.0) == pytest.approx(-50.0)
        assert fluent_my_to_aero(-30.0) == pytest.approx(30.0)

    def test_array_input(self):
        my_fluent = np.array([10.0, -20.0, 0.0])
        result = fluent_my_to_aero(my_fluent)
        assert np.allclose(result, np.array([-10.0, 20.0, 0.0]))
