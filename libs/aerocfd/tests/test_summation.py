import numpy as np
import pytest

from aerocfd.analysis.summation import group_names, my_sum, wind_force_sum
from aerocfd.models.alpha_case import AlphaCase
from aerocfd.models.part_load import PartLoad


def _parts():
    return [
        PartLoad("wing", "Wing", fx_n=-10.0, fz_n=800.0, my_nm=5.0),
        PartLoad("fuselage", "Fuselage", fx_n=-5.0, fz_n=200.0, my_nm=-2.0),
    ]


def test_wind_force_sum_all_parts_at_zero_alpha():
    # At α=0: drag = -Fx, lift = Fz, summed over parts.
    drag, lift = wind_force_sum(_parts(), alpha_deg=0.0, group=None)
    assert drag == pytest.approx(15.0)    # -(-10) + -(-5)
    assert lift == pytest.approx(1000.0)  # 800 + 200


def test_wind_force_sum_filters_to_group():
    drag, lift = wind_force_sum(_parts(), alpha_deg=0.0, group="Wing")
    assert drag == pytest.approx(10.0)
    assert lift == pytest.approx(800.0)


def test_my_sum_total_and_group():
    assert my_sum(_parts(), group=None) == pytest.approx(3.0)
    assert my_sum(_parts(), group="Wing") == pytest.approx(5.0)


def test_group_names_unique_first_seen_order():
    cases = [
        AlphaCase(alpha_deg=0.0, part_loads=_parts()),
        AlphaCase(alpha_deg=5.0, part_loads=[PartLoad("tail", "Tail", 0.0, 0.0, 0.0)]),
    ]
    assert group_names(cases) == ["Wing", "Fuselage", "Tail"]
