import pytest
from dataclasses import FrozenInstanceError

from aerocfd.models.alpha_case import AlphaCase, ConvergenceStatus


class TestConvergenceStatus:
    def test_has_expected_members(self):
        names = {s.name for s in ConvergenceStatus}
        assert names == {
            "CONVERGED", "PARTIALLY_CONVERGED", "OSCILLATING",
            "DIVERGED", "STOPPED_MANUALLY", "UNKNOWN",
        }


class TestAlphaCase:
    def test_construct_minimal(self):
        case = AlphaCase(alpha_deg=5.0, fx_n=-100.0, fz_n=1000.0, my_nm=50.0)
        assert case.alpha_deg == pytest.approx(5.0)
        assert case.convergence_status == ConvergenceStatus.UNKNOWN

    def test_is_frozen(self):
        case = AlphaCase(alpha_deg=5.0, fx_n=0.0, fz_n=0.0, my_nm=0.0)
        with pytest.raises(FrozenInstanceError):
            case.alpha_deg = 10.0
