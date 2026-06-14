"""CRUD smoke tests for AeroCfdDatabase against a temporary SQLite file."""

import pytest

from aerisvault.modules.aerocfd.core.database import AeroCfdDatabase
from aerisvault.modules.aerocfd.core.mappers import build_dataset


@pytest.fixture
def db(tmp_path):
    return AeroCfdDatabase(f"sqlite:///{tmp_path / 'aerocfd_test.db'}")


@pytest.fixture
def aircraft_with_parts(db):
    aircraft = db.create_aircraft(name="Glider", s_ref_m2=10.0, c_ref_m=1.5, b_ref_m=8.0)
    wing = db.add_part(aircraft.id, name="wing", group_name="Wing")
    tail = db.add_part(aircraft.id, name="tail", group_name="Tail")
    return aircraft, wing, tail


def test_create_and_list_aircraft(db):
    db.create_aircraft(name="Glider", s_ref_m2=12.0, c_ref_m=1.2, b_ref_m=10.0)
    aircraft = db.list_aircraft()
    assert len(aircraft) == 1 and aircraft[0].name == "Glider"


def test_parts_listed_in_order(aircraft_with_parts, db):
    aircraft, _, _ = aircraft_with_parts
    parts = db.list_parts(aircraft.id)
    assert [(p.name, p.group_name) for p in parts] == [("wing", "Wing"), ("tail", "Tail")]


def test_set_alpha_case_is_idempotent(aircraft_with_parts, db):
    aircraft, wing, tail = aircraft_with_parts
    oc = db.create_operating_condition(aircraft.id, name="oc", velocity_mps=50.0, density_kgpm3=1.225)
    loads = [
        {"part_id": wing.id, "fx_n": -15.0, "fz_n": 700.0, "my_nm": 25.0},
        {"part_id": tail.id, "fx_n": -2.0, "fz_n": 20.0, "my_nm": -8.0},
    ]
    db.set_alpha_case(oc.id, 5.0, loads)
    db.set_alpha_case(oc.id, 5.0, loads)  # saving again must not duplicate
    cases = db.list_alpha_cases(oc.id)
    assert len(cases) == 1
    assert len(cases[0].part_loads) == 2


def test_round_trip_db_to_dataset_groups(aircraft_with_parts, db):
    aircraft, wing, tail = aircraft_with_parts
    oc = db.create_operating_condition(aircraft.id, name="oc", velocity_mps=50.0, density_kgpm3=1.225)
    db.set_alpha_case(oc.id, 0.0, [
        {"part_id": wing.id, "fx_n": -10.0, "fz_n": 200.0, "my_nm": 0.0},
        {"part_id": tail.id, "fx_n": -2.0, "fz_n": 20.0, "my_nm": 0.0},
    ])
    db.set_alpha_case(oc.id, 5.0, [
        {"part_id": wing.id, "fx_n": -15.0, "fz_n": 700.0, "my_nm": 25.0},
        {"part_id": tail.id, "fx_n": -2.0, "fz_n": 20.0, "my_nm": -8.0},
    ])
    dataset = build_dataset(aircraft, db.get_operating_condition(oc.id), db.list_alpha_cases(oc.id))
    assert dataset.groups() == ["Wing", "Tail"]
    assert dataset.cd().values[0] > 0.0  # CD(α=0) > 0 gold invariant, end to end


def test_delete_part_cascades_its_loads(aircraft_with_parts, db):
    aircraft, wing, tail = aircraft_with_parts
    oc = db.create_operating_condition(aircraft.id, name="oc", velocity_mps=50.0, density_kgpm3=1.225)
    db.set_alpha_case(oc.id, 0.0, [
        {"part_id": wing.id, "fx_n": -10.0, "fz_n": 200.0, "my_nm": 0.0},
        {"part_id": tail.id, "fx_n": -2.0, "fz_n": 20.0, "my_nm": 0.0},
    ])
    assert db.delete_part(wing.id) is True
    case = db.list_alpha_cases(oc.id)[0]
    assert [pl.part.name for pl in case.part_loads] == ["tail"]


def test_delete_aircraft_cascades_everything(aircraft_with_parts, db):
    aircraft, wing, _ = aircraft_with_parts
    oc = db.create_operating_condition(aircraft.id, name="oc", velocity_mps=50.0, density_kgpm3=1.225)
    db.set_alpha_case(oc.id, 0.0, [{"part_id": wing.id, "fx_n": -10.0, "fz_n": 200.0, "my_nm": 0.0}])
    assert db.delete_aircraft(aircraft.id) is True
    assert db.list_aircraft() == []
    assert db.list_parts(aircraft.id) == []
    assert db.list_operating_conditions(aircraft.id) == []
