"""Round-trip tests: ORM rows map to the library dataclasses the engine expects."""

from aerocfd.models.aircraft import Aircraft
from aerocfd.models.alpha_case import AlphaCase, ConvergenceStatus
from aerocfd.models.dataset import AeroDataset
from aerocfd.models.operating_condition import OperatingCondition

from aerisvault.modules.aerocfd.core.models import (
    AircraftORM, AlphaCaseORM, OperatingConditionORM,
)
from aerisvault.modules.aerocfd.core.mappers import (
    aircraft_to_dataclass, alpha_case_to_dataclass, build_dataset,
    operating_condition_to_dataclass,
)


def test_aircraft_orm_maps_to_dataclass():
    orm = AircraftORM(
        name="Glider", description="test", s_ref_m2=12.0, c_ref_m=1.2,
        b_ref_m=10.0, axis_convention="x_fwd_z_up_rh",
    )
    ac = aircraft_to_dataclass(orm)
    assert isinstance(ac, Aircraft)
    assert (ac.name, ac.s_ref_m2, ac.c_ref_m, ac.b_ref_m) == ("Glider", 12.0, 1.2, 10.0)


def test_operating_condition_orm_maps_to_dataclass():
    orm = OperatingConditionORM(
        aircraft_id=1, name="SL_60", velocity_mps=60.0, density_kgpm3=1.225,
    )
    oc = operating_condition_to_dataclass(orm)
    assert isinstance(oc, OperatingCondition)
    assert (oc.name, oc.velocity_mps, oc.density_kgpm3) == ("SL_60", 60.0, 1.225)


def test_alpha_case_orm_maps_to_dataclass_with_enum():
    orm = AlphaCaseORM(
        operating_condition_id=1, alpha_deg=5.0, fx_n=-15.0, fz_n=700.0,
        my_nm=25.0, convergence_status="converged",
    )
    case = alpha_case_to_dataclass(orm)
    assert isinstance(case, AlphaCase)
    assert case.convergence_status is ConvergenceStatus.CONVERGED
    assert (case.alpha_deg, case.fx_n, case.fz_n, case.my_nm) == (5.0, -15.0, 700.0, 25.0)


def test_build_dataset_produces_working_aerodataset():
    aircraft = AircraftORM(name="A", s_ref_m2=10.0, c_ref_m=1.5, b_ref_m=8.0)
    oc = OperatingConditionORM(aircraft_id=1, name="oc", velocity_mps=50.0, density_kgpm3=1.225)
    cases = [
        AlphaCaseORM(operating_condition_id=1, alpha_deg=0.0, fx_n=-10.0, fz_n=200.0, my_nm=0.0),
        AlphaCaseORM(operating_condition_id=1, alpha_deg=5.0, fx_n=-15.0, fz_n=700.0, my_nm=25.0),
    ]
    dataset = build_dataset(aircraft, oc, cases)
    assert isinstance(dataset, AeroDataset)
    # gold-test invariant survives the mapping seam: CD(α=0) > 0 for a draggy body
    cd = dataset.cd()
    idx = int((cd.alpha_deg == 0.0).nonzero()[0][0])
    assert cd.values[idx] > 0.0
