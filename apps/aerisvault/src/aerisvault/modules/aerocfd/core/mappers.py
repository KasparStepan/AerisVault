"""Translate aerocfd ORM rows to/from the pure library dataclasses.

The library (`aerocfd`) knows nothing about SQLAlchemy. These mappers are the
single seam between storage (ORM) and computation (frozen dataclasses). Only the
fields the library cares about cross the seam; storage-only metadata (turbulence
settings, timestamps, iteration counts) stays in the ORM.
"""
from __future__ import annotations

from aerocfd.models.aircraft import Aircraft
from aerocfd.models.alpha_case import AlphaCase, ConvergenceStatus
from aerocfd.models.dataset import AeroDataset
from aerocfd.models.operating_condition import OperatingCondition
from aerocfd.models.part_load import PartLoad

from aerisvault.modules.aerocfd.core.models import (
    AircraftORM, AlphaCaseORM, OperatingConditionORM,
)


def aircraft_to_dataclass(orm: AircraftORM) -> Aircraft:
    return Aircraft(
        name=orm.name,
        s_ref_m2=orm.s_ref_m2,
        c_ref_m=orm.c_ref_m,
        b_ref_m=orm.b_ref_m,
        axis_convention=orm.axis_convention,
        description=orm.description or "",
    )


def operating_condition_to_dataclass(orm: OperatingConditionORM) -> OperatingCondition:
    return OperatingCondition(
        name=orm.name,
        velocity_mps=orm.velocity_mps,
        density_kgpm3=orm.density_kgpm3,
        description=orm.description or "",
    )


def alpha_case_to_dataclass(orm: AlphaCaseORM) -> AlphaCase:
    """Build an AlphaCase with one PartLoad per stored part load.

    Each load row is joined to its part for the part name and group, which the
    library needs for per-group summation.
    """
    part_loads = tuple(
        PartLoad(
            part_name=load.part.name,
            group=load.part.group_name,
            fx_n=load.fx_n,
            fz_n=load.fz_n,
            my_nm=load.my_nm,
            moments=tuple(
                (moment.reference_point.label, moment.my_nm) for moment in load.moments
            ),
        )
        for load in orm.part_loads
    )
    return AlphaCase(
        alpha_deg=orm.alpha_deg,
        part_loads=part_loads,
        convergence_status=ConvergenceStatus(orm.convergence_status or "unknown"),
        notes=orm.notes or "",
    )


def build_dataset(
    aircraft_orm: AircraftORM,
    operating_condition_orm: OperatingConditionORM,
    alpha_case_orms: list[AlphaCaseORM],
) -> AeroDataset:
    """Assemble an AeroDataset from ORM rows for analysis/plotting."""
    return AeroDataset(
        aircraft=aircraft_to_dataclass(aircraft_orm),
        operating_condition=operating_condition_to_dataclass(operating_condition_orm),
        alpha_cases=[alpha_case_to_dataclass(c) for c in alpha_case_orms],
    )
