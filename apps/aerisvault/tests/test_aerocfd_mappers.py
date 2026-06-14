"""Round-trip tests: ORM rows map to the library dataclasses the engine expects."""

from aerocfd.models.aircraft import Aircraft
from aerocfd.models.alpha_case import AlphaCase, ConvergenceStatus
from aerocfd.models.dataset import AeroDataset
from aerocfd.models.operating_condition import OperatingCondition

from aerisvault.modules.aerocfd.core.models import (
    AircraftORM, AircraftPartORM, AlphaCaseORM, AlphaCasePartLoadORM,
    AlphaCasePartLoadMomentORM, MomentReferencePointORM, OperatingConditionORM,
)
from aerisvault.modules.aerocfd.core.mappers import (
    aircraft_to_dataclass, alpha_case_to_dataclass, build_dataset,
    operating_condition_to_dataclass,
)


def _load(part_name, group, fx, fz, my):
    """A transient part-load ORM with its part attached (as the DB would join it)."""
    part = AircraftPartORM(name=part_name, group_name=group)
    return AlphaCasePartLoadORM(fx_n=fx, fz_n=fz, my_nm=my, part=part)


def test_aircraft_orm_maps_to_dataclass():
    orm = AircraftORM(
        name="Glider", description="test", s_ref_m2=12.0, c_ref_m=1.2,
        b_ref_m=10.0, axis_convention="x_fwd_z_up_rh",
    )
    ac = aircraft_to_dataclass(orm)
    assert isinstance(ac, Aircraft)
    assert (ac.name, ac.s_ref_m2, ac.c_ref_m, ac.b_ref_m) == ("Glider", 12.0, 1.2, 10.0)


def test_operating_condition_orm_maps_to_dataclass():
    orm = OperatingConditionORM(aircraft_id=1, name="SL_60", velocity_mps=60.0, density_kgpm3=1.225)
    oc = operating_condition_to_dataclass(orm)
    assert isinstance(oc, OperatingCondition)
    assert (oc.name, oc.velocity_mps, oc.density_kgpm3) == ("SL_60", 60.0, 1.225)


def test_alpha_case_maps_part_loads_with_group():
    case = AlphaCaseORM(
        alpha_deg=5.0, convergence_status="converged",
        part_loads=[_load("wing", "Wing", -15.0, 700.0, 25.0),
                    _load("fuselage", "Fuselage", -5.0, 100.0, -3.0)],
    )
    dc = alpha_case_to_dataclass(case)
    assert isinstance(dc, AlphaCase)
    assert dc.convergence_status is ConvergenceStatus.CONVERGED
    assert {p.group for p in dc.part_loads} == {"Wing", "Fuselage"}
    # totals are summed from the parts
    assert dc.total_fz_n == 800.0
    assert dc.total_fx_n == -20.0


def test_alpha_case_maps_per_reference_moments():
    ref20 = MomentReferencePointORM(label="20% MAC")
    ref25 = MomentReferencePointORM(label="25% MAC")
    part = AircraftPartORM(name="wing", group_name="Wing")
    load = AlphaCasePartLoadORM(fx_n=-10.0, fz_n=800.0, part=part, moments=[
        AlphaCasePartLoadMomentORM(my_nm=5.0, reference_point=ref20),
        AlphaCasePartLoadMomentORM(my_nm=4.0, reference_point=ref25),
    ])
    case = AlphaCaseORM(alpha_deg=5.0, part_loads=[load])
    dc = alpha_case_to_dataclass(case)
    moment_load = dc.part_loads[0]
    assert moment_load.moment_for("20% MAC") == 5.0
    assert moment_load.moment_for("25% MAC") == 4.0


def test_build_dataset_groups_sum_to_total():
    aircraft = AircraftORM(name="A", s_ref_m2=10.0, c_ref_m=1.5, b_ref_m=8.0)
    oc = OperatingConditionORM(aircraft_id=1, name="oc", velocity_mps=50.0, density_kgpm3=1.225)
    cases = [
        AlphaCaseORM(alpha_deg=0.0, part_loads=[
            _load("wing", "Wing", -10.0, 200.0, 0.0), _load("tail", "Tail", -2.0, 20.0, 0.0)]),
        AlphaCaseORM(alpha_deg=5.0, part_loads=[
            _load("wing", "Wing", -15.0, 700.0, 25.0), _load("tail", "Tail", -2.0, 20.0, -8.0)]),
    ]
    dataset = build_dataset(aircraft, oc, cases)
    assert isinstance(dataset, AeroDataset)
    assert dataset.groups() == ["Wing", "Tail"]
    # group CLs sum to the total CL, and CD(α=0) > 0 (gold invariant) survives the seam
    total_cl = dataset.cl().values
    group_cl = dataset.cl(group="Wing").values + dataset.cl(group="Tail").values
    assert (abs(total_cl - group_cl) < 1e-9).all()
    assert dataset.cd().values[0] > 0.0
