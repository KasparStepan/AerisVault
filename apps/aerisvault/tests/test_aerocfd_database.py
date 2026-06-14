"""CRUD smoke tests for AeroCfdDatabase against a temporary SQLite file."""

import pytest

from aerisvault.modules.aerocfd.core.database import AeroCfdDatabase


@pytest.fixture
def db(tmp_path):
    return AeroCfdDatabase(f"sqlite:///{tmp_path / 'aerocfd_test.db'}")


def test_create_and_list_aircraft(db):
    db.create_aircraft(name="Glider", s_ref_m2=12.0, c_ref_m=1.2, b_ref_m=10.0)
    aircraft = db.list_aircraft()
    assert len(aircraft) == 1
    assert aircraft[0].name == "Glider"


def test_update_aircraft_ref_values(db):
    ac = db.create_aircraft(name="A", s_ref_m2=10.0, c_ref_m=1.5, b_ref_m=8.0)
    assert db.update_aircraft(ac.id, s_ref_m2=11.0) is True
    assert db.get_aircraft(ac.id).s_ref_m2 == pytest.approx(11.0)


def test_operating_conditions_scoped_to_aircraft(db):
    a1 = db.create_aircraft(name="A1", s_ref_m2=10.0, c_ref_m=1.5, b_ref_m=8.0)
    a2 = db.create_aircraft(name="A2", s_ref_m2=10.0, c_ref_m=1.5, b_ref_m=8.0)
    db.create_operating_condition(a1.id, name="oc1", velocity_mps=50.0, density_kgpm3=1.225)
    assert len(db.list_operating_conditions(a1.id)) == 1
    assert len(db.list_operating_conditions(a2.id)) == 0


def test_replace_alpha_cases_is_wholesale(db):
    a = db.create_aircraft(name="A", s_ref_m2=10.0, c_ref_m=1.5, b_ref_m=8.0)
    oc = db.create_operating_condition(a.id, name="oc", velocity_mps=50.0, density_kgpm3=1.225)
    db.replace_alpha_cases(oc.id, [
        {"alpha_deg": 0.0, "fx_n": -10.0, "fz_n": 200.0, "my_nm": 0.0},
        {"alpha_deg": 5.0, "fx_n": -15.0, "fz_n": 700.0, "my_nm": 25.0},
    ])
    assert len(db.list_alpha_cases(oc.id)) == 2
    # Replacing again leaves only the new set (no accumulation), sorted by alpha.
    db.replace_alpha_cases(oc.id, [{"alpha_deg": 10.0, "fx_n": -30.0, "fz_n": 1200.0, "my_nm": 50.0}])
    cases = db.list_alpha_cases(oc.id)
    assert len(cases) == 1
    assert cases[0].alpha_deg == pytest.approx(10.0)


def test_delete_aircraft_cascades(db):
    a = db.create_aircraft(name="A", s_ref_m2=10.0, c_ref_m=1.5, b_ref_m=8.0)
    oc = db.create_operating_condition(a.id, name="oc", velocity_mps=50.0, density_kgpm3=1.225)
    db.replace_alpha_cases(oc.id, [{"alpha_deg": 0.0, "fx_n": -10.0, "fz_n": 200.0, "my_nm": 0.0}])
    assert db.delete_aircraft(a.id) is True
    assert db.list_aircraft() == []
    # cascade removed the operating condition and its alpha cases
    assert db.list_operating_conditions(a.id) == []
    assert db.list_alpha_cases(oc.id) == []
