import numpy as np
import pytest

from aerocfd.models.aircraft import Aircraft
from aerocfd.models.alpha_case import AlphaCase
from aerocfd.models.operating_condition import OperatingCondition
from aerocfd.models.dataset import AeroDataset
from aerocfd.models.part_load import PartLoad
from aerocfd.models.polar import Polar


@pytest.fixture
def reference_dataset(reference_aircraft_kwargs, reference_operating_condition_kwargs,
                      stable_airfoil_alpha_cases):
    aircraft = Aircraft(**reference_aircraft_kwargs)
    oc = OperatingCondition(**reference_operating_condition_kwargs)
    return AeroDataset(aircraft=aircraft, operating_condition=oc,
                       alpha_cases=stable_airfoil_alpha_cases)


class TestAeroDatasetBasics:
    def test_alpha_deg_is_sorted_array(self, reference_dataset):
        alpha = reference_dataset.alpha_deg
        assert isinstance(alpha, np.ndarray)
        assert np.all(np.diff(alpha) > 0)

    def test_dynamic_pressure(self, reference_dataset):
        # q = 0.5 · 1.225 · 50² = 1531.25 Pa
        assert reference_dataset.dynamic_pressure_pa == pytest.approx(1531.25)


class TestAeroDatasetPolars:
    def test_lift_is_polar(self, reference_dataset):
        assert isinstance(reference_dataset.lift(), Polar)

    def test_cl_is_dimensionless(self, reference_dataset):
        polar = reference_dataset.cl()
        assert polar.units == "-"

    def test_lift_to_drag_at_zero_alpha_matches_lift_over_drag(self, reference_dataset):
        ld = reference_dataset.lift_to_drag()
        lift = reference_dataset.lift()
        drag = reference_dataset.drag()
        idx = np.where(reference_dataset.alpha_deg == 0.0)[0][0]
        assert ld.values[idx] == pytest.approx(lift.values[idx] / drag.values[idx])


class TestStableAirfoilGoldStandard:
    """Gold test #3: Cm sign-flip regression — Cm negative for positive α
    on the synthetic stable airfoil (My_fluent = 5·α by construction, so this
    can only fail if the fluent_my_to_aero sign flip is dropped)."""

    def test_cm_is_negative_at_positive_alpha(self, reference_dataset):
        cm_polar = reference_dataset.cm()
        for alpha, cm_value in zip(cm_polar.alpha_deg, cm_polar.values):
            if alpha > 0:
                assert cm_value < 0, (
                    f"Cm sign-flip regression failed at α={alpha}°: Cm={cm_value} "
                    "should be negative (nose-down). Sign flip likely missing."
                )


class TestPositiveDragGoldStandard:
    """Gold test #4: CD at α=0 must be strictly positive for a draggy aircraft.

    This is the invariant that catches an Fx-sign error in body_to_wind —
    gold test #2 (Fx=0) cannot, because its Fx term vanishes. The sample
    fixture uses negative fx_n (Fluent reports drag as a -X force on the body),
    so a correct rotation yields positive CD at α=0.
    """

    def test_cd_is_positive_at_zero_alpha(self, reference_dataset):
        cd_polar = reference_dataset.cd()
        idx = int(np.where(cd_polar.alpha_deg == 0.0)[0][0])
        assert cd_polar.values[idx] > 0.0, (
            f"CD(α=0) = {cd_polar.values[idx]} must be > 0. A non-positive value "
            "means the body→wind Fx sign is wrong."
        )


@pytest.fixture
def parted_dataset(reference_aircraft_kwargs, reference_operating_condition_kwargs):
    """A two-group dataset (Wing + Tail) for testing per-group decomposition."""
    aircraft = Aircraft(**reference_aircraft_kwargs)
    oc = OperatingCondition(**reference_operating_condition_kwargs)
    cases = []
    for alpha in [0.0, 5.0, 10.0]:
        parts = [
            PartLoad("wing", "Wing", fx_n=-10.0, fz_n=100.0 * alpha + 200.0, my_nm=5.0 * alpha),
            PartLoad("tail", "Tail", fx_n=-2.0, fz_n=20.0, my_nm=-3.0 * alpha),
        ]
        cases.append(AlphaCase(alpha_deg=alpha, part_loads=parts))
    return AeroDataset(aircraft=aircraft, operating_condition=oc, alpha_cases=cases)


class TestGroupDecomposition:
    """Per-part feature: the group contributions must sum to the total
    (coefficients add at a fixed S_ref) — the invariant the whole feature rests on."""

    def test_groups_listed_in_order(self, parted_dataset):
        assert parted_dataset.groups() == ["Wing", "Tail"]

    def test_group_lifts_sum_to_total(self, parted_dataset):
        total = parted_dataset.lift().values
        groups = parted_dataset.lift(group="Wing").values + parted_dataset.lift(group="Tail").values
        assert np.allclose(total, groups)

    def test_group_cl_sums_to_total_cl(self, parted_dataset):
        total = parted_dataset.cl().values
        groups = parted_dataset.cl(group="Wing").values + parted_dataset.cl(group="Tail").values
        assert np.allclose(total, groups)

    def test_group_cm_sums_to_total_cm(self, parted_dataset):
        total = parted_dataset.cm().values
        groups = parted_dataset.cm(group="Wing").values + parted_dataset.cm(group="Tail").values
        assert np.allclose(total, groups)

    def test_total_drag_positive_at_zero_alpha(self, parted_dataset):
        # Summed parts still satisfy the CD(α=0) > 0 gold invariant.
        cd_polar = parted_dataset.cd()
        idx = int(np.where(cd_polar.alpha_deg == 0.0)[0][0])
        assert cd_polar.values[idx] > 0.0
