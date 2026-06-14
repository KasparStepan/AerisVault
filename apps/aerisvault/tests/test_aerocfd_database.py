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


def test_create_aircraft_seeds_default_reference_points(db):
    aircraft = db.create_aircraft(name="A", s_ref_m2=10.0, c_ref_m=1.5, b_ref_m=8.0)
    labels = [r.label for r in db.list_reference_points(aircraft.id)]
    assert labels == ["20% MAC", "25% MAC", "30% MAC"]


def test_reference_point_crud(aircraft_with_parts, db):
    aircraft, _, _ = aircraft_with_parts
    new = db.add_reference_point(aircraft.id, "40% MAC")
    assert "40% MAC" in [r.label for r in db.list_reference_points(aircraft.id)]
    db.update_reference_point(new.id, "35% MAC")
    db.delete_reference_point(new.id)
    assert "35% MAC" not in [r.label for r in db.list_reference_points(aircraft.id)]


def test_moments_per_reference_round_trip(aircraft_with_parts, db):
    aircraft, wing, tail = aircraft_with_parts
    refs = db.list_reference_points(aircraft.id)  # the three seeded points
    oc = db.create_operating_condition(aircraft.id, name="oc", velocity_mps=50.0, density_kgpm3=1.225)
    db.set_alpha_case(oc.id, 5.0, [
        {"part_id": wing.id, "fx_n": -15.0, "fz_n": 700.0,
         "moments": {refs[0].id: 25.0, refs[1].id: 20.0, refs[2].id: 16.0}},
        {"part_id": tail.id, "fx_n": -2.0, "fz_n": 20.0,
         "moments": {refs[0].id: -8.0, refs[1].id: -10.0, refs[2].id: -12.0}},
    ])
    # build a second α so the dataset has a polar
    db.set_alpha_case(oc.id, 0.0, [
        {"part_id": wing.id, "fx_n": -10.0, "fz_n": 200.0,
         "moments": {refs[0].id: 0.0, refs[1].id: 0.0, refs[2].id: 0.0}},
        {"part_id": tail.id, "fx_n": -2.0, "fz_n": 20.0,
         "moments": {refs[0].id: 0.0, refs[1].id: 0.0, refs[2].id: 0.0}},
    ])
    dataset = build_dataset(aircraft, db.get_operating_condition(oc.id), db.list_alpha_cases(oc.id))
    assert dataset.reference_points() == ["20% MAC", "25% MAC", "30% MAC"]
    # Cm differs between references (moments differ); group Cm sums to total at a ref
    cm20 = dataset.cm(reference="20% MAC").values
    cm25 = dataset.cm(reference="25% MAC").values
    assert cm20[-1] != cm25[-1]
    group_sum = dataset.cm(group="Wing", reference="20% MAC").values + dataset.cm(group="Tail", reference="20% MAC").values
    assert (abs(cm20 - group_sum) < 1e-9).all()


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
