import pytest
from dataclasses import FrozenInstanceError

from aerocfd.models.operating_condition import OperatingCondition


class TestOperatingCondition:
    def test_construct(self, reference_operating_condition_kwargs):
        oc = OperatingCondition(**reference_operating_condition_kwargs)
        assert oc.name == "SL_50mps"
        assert oc.velocity_mps == pytest.approx(50.0)
        assert oc.density_kgpm3 == pytest.approx(1.225)

    def test_is_frozen(self, reference_operating_condition_kwargs):
        oc = OperatingCondition(**reference_operating_condition_kwargs)
        with pytest.raises(FrozenInstanceError):
            oc.velocity_mps = 80.0
