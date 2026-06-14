import pytest
from dataclasses import FrozenInstanceError

from aerocfd.models.aircraft import Aircraft


class TestAircraft:
    def test_construct_with_required_fields(self, reference_aircraft_kwargs):
        ac = Aircraft(**reference_aircraft_kwargs)
        assert ac.name == "Reference"
        assert ac.s_ref_m2 == pytest.approx(10.0)
        assert ac.axis_convention == "x_fwd_z_up_rh"

    def test_is_frozen(self, reference_aircraft_kwargs):
        ac = Aircraft(**reference_aircraft_kwargs)
        with pytest.raises(FrozenInstanceError):
            ac.s_ref_m2 = 20.0
