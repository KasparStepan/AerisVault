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
