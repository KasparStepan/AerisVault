import pytest
from dataclasses import FrozenInstanceError

from aerocfd.models.part_load import PartLoad


def test_fields():
    load = PartLoad(part_name="wing", group="Wing", fx_n=-10.0, fz_n=800.0, my_nm=5.0)
    assert load.part_name == "wing"
    assert load.group == "Wing"
    assert (load.fx_n, load.fz_n, load.my_nm) == (-10.0, 800.0, 5.0)


def test_is_frozen():
    load = PartLoad("wing", "Wing", 0.0, 0.0, 0.0)
    with pytest.raises(FrozenInstanceError):
        load.fx_n = 1.0


def test_moment_for_single_reference_fallback():
    # No per-reference moments → moment_for(None) is the single my_nm.
    load = PartLoad("wing", "Wing", 0.0, 0.0, my_nm=7.0)
    assert load.moment_for(None) == 7.0


def test_moment_for_named_references():
    load = PartLoad("wing", "Wing", 0.0, 0.0,
                    moments=[("20% MAC", 5.0), ("25% MAC", 4.0)])
    assert load.moment_for("20% MAC") == 5.0
    assert load.moment_for("25% MAC") == 4.0
    assert load.moment_for("99% MAC") == 0.0  # unknown reference → 0
