"""aerocfd module — SQLite/SQLAlchemy persistence.

Mirrors the FSI SimulationDatabase session pattern exactly: expire_on_commit=False
plus selectinload on list/get queries, so ORM objects stay usable after the
session closes (Streamlit renders them outside the session scope).
"""
from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from aerisvault.modules.aerocfd.core.models import (
    AircraftORM, AircraftPartORM, AlphaCaseORM, AlphaCasePartLoadORM,
    AlphaCasePartLoadMomentORM, Base, MomentReferencePointORM, OperatingConditionORM,
)

# Moment reference points every new aircraft starts with (editable afterwards).
DEFAULT_MOMENT_REFERENCE_LABELS = ["20% MAC", "25% MAC", "30% MAC"]

logger = logging.getLogger(__name__)


class AeroCfdDatabase:
    """Manager for the aerocfd aircraft / parts / operating-condition / alpha-case database."""

    def __init__(self, db_url: str = "sqlite:///aerocfd.db"):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    # --- Aircraft ---

    def create_aircraft(
        self, name: str, s_ref_m2: float, c_ref_m: float, b_ref_m: float,
        description: str = "", axis_convention: str = "x_fwd_z_up_rh",
    ) -> AircraftORM:
        with self.get_session() as session:
            aircraft = AircraftORM(
                name=name, s_ref_m2=s_ref_m2, c_ref_m=c_ref_m, b_ref_m=b_ref_m,
                description=description, axis_convention=axis_convention,
            )
            # Seed the standard moment reference points; the user can edit them.
            aircraft.moment_reference_points = [
                MomentReferencePointORM(label=label, display_order=order)
                for order, label in enumerate(DEFAULT_MOMENT_REFERENCE_LABELS)
            ]
            session.add(aircraft)
            session.commit()
            session.refresh(aircraft)
            return aircraft

    def list_aircraft(self) -> List[AircraftORM]:
        with self.get_session() as session:
            stmt = (
                select(AircraftORM)
                .order_by(AircraftORM.created_at.desc())
                .options(
                    selectinload(AircraftORM.operating_conditions),
                    selectinload(AircraftORM.parts),
                    selectinload(AircraftORM.moment_reference_points),
                )
            )
            return list(session.scalars(stmt).all())

    def get_aircraft(self, aircraft_id: int) -> Optional[AircraftORM]:
        with self.get_session() as session:
            stmt = (
                select(AircraftORM)
                .where(AircraftORM.id == aircraft_id)
                .options(
                    selectinload(AircraftORM.operating_conditions),
                    selectinload(AircraftORM.parts),
                    selectinload(AircraftORM.moment_reference_points),
                )
            )
            return session.scalar(stmt)

    def update_aircraft(self, aircraft_id: int, **fields) -> bool:
        with self.get_session() as session:
            aircraft = session.get(AircraftORM, aircraft_id)
            if not aircraft:
                return False
            for key, value in fields.items():
                setattr(aircraft, key, value)
            session.commit()
            return True

    def delete_aircraft(self, aircraft_id: int) -> bool:
        with self.get_session() as session:
            aircraft = session.get(AircraftORM, aircraft_id)
            if not aircraft:
                return False
            session.delete(aircraft)
            session.commit()
            return True

    # --- Parts ---

    def add_part(self, aircraft_id: int, name: str, group_name: str) -> AircraftPartORM:
        with self.get_session() as session:
            order = len(self.list_parts(aircraft_id))
            part = AircraftPartORM(
                aircraft_id=aircraft_id, name=name, group_name=group_name, display_order=order,
            )
            session.add(part)
            session.commit()
            session.refresh(part)
            return part

    def list_parts(self, aircraft_id: int) -> List[AircraftPartORM]:
        with self.get_session() as session:
            stmt = (
                select(AircraftPartORM)
                .where(AircraftPartORM.aircraft_id == aircraft_id)
                .order_by(AircraftPartORM.display_order, AircraftPartORM.id)
            )
            return list(session.scalars(stmt).all())

    def update_part(self, part_id: int, **fields) -> bool:
        with self.get_session() as session:
            part = session.get(AircraftPartORM, part_id)
            if not part:
                return False
            for key, value in fields.items():
                setattr(part, key, value)
            session.commit()
            return True

    def delete_part(self, part_id: int) -> bool:
        with self.get_session() as session:
            part = session.get(AircraftPartORM, part_id)
            if not part:
                return False
            session.delete(part)
            session.commit()
            return True

    # --- Moment reference points ---

    def list_reference_points(self, aircraft_id: int) -> List[MomentReferencePointORM]:
        with self.get_session() as session:
            stmt = (
                select(MomentReferencePointORM)
                .where(MomentReferencePointORM.aircraft_id == aircraft_id)
                .order_by(MomentReferencePointORM.display_order, MomentReferencePointORM.id)
            )
            return list(session.scalars(stmt).all())

    def add_reference_point(self, aircraft_id: int, label: str) -> MomentReferencePointORM:
        with self.get_session() as session:
            order = len(self.list_reference_points(aircraft_id))
            ref = MomentReferencePointORM(aircraft_id=aircraft_id, label=label, display_order=order)
            session.add(ref)
            session.commit()
            session.refresh(ref)
            return ref

    def update_reference_point(self, reference_point_id: int, label: str) -> bool:
        with self.get_session() as session:
            ref = session.get(MomentReferencePointORM, reference_point_id)
            if not ref:
                return False
            ref.label = label
            session.commit()
            return True

    def delete_reference_point(self, reference_point_id: int) -> bool:
        with self.get_session() as session:
            ref = session.get(MomentReferencePointORM, reference_point_id)
            if not ref:
                return False
            session.delete(ref)
            session.commit()
            return True

    # --- Operating conditions ---

    def create_operating_condition(
        self, aircraft_id: int, name: str, velocity_mps: float, density_kgpm3: float,
        description: str = "", **optional_fields,
    ) -> OperatingConditionORM:
        with self.get_session() as session:
            oc = OperatingConditionORM(
                aircraft_id=aircraft_id, name=name, velocity_mps=velocity_mps,
                density_kgpm3=density_kgpm3, description=description, **optional_fields,
            )
            session.add(oc)
            session.commit()
            session.refresh(oc)
            return oc

    def list_operating_conditions(self, aircraft_id: int) -> List[OperatingConditionORM]:
        with self.get_session() as session:
            stmt = (
                select(OperatingConditionORM)
                .where(OperatingConditionORM.aircraft_id == aircraft_id)
                .order_by(OperatingConditionORM.id)
                .options(selectinload(OperatingConditionORM.alpha_cases))
            )
            return list(session.scalars(stmt).all())

    def get_operating_condition(self, oc_id: int) -> Optional[OperatingConditionORM]:
        with self.get_session() as session:
            stmt = (
                select(OperatingConditionORM)
                .where(OperatingConditionORM.id == oc_id)
                .options(selectinload(OperatingConditionORM.alpha_cases))
            )
            return session.scalar(stmt)

    def delete_operating_condition(self, oc_id: int) -> bool:
        with self.get_session() as session:
            oc = session.get(OperatingConditionORM, oc_id)
            if not oc:
                return False
            session.delete(oc)
            session.commit()
            return True

    # --- Alpha cases (with per-part loads) ---

    def list_alpha_cases(self, oc_id: int) -> List[AlphaCaseORM]:
        """All α cases for an operating condition, with their part loads and the
        part each load belongs to (for name + group)."""
        with self.get_session() as session:
            stmt = (
                select(AlphaCaseORM)
                .where(AlphaCaseORM.operating_condition_id == oc_id)
                .order_by(AlphaCaseORM.alpha_deg)
                .options(
                    selectinload(AlphaCaseORM.part_loads).selectinload(AlphaCasePartLoadORM.part),
                    selectinload(AlphaCaseORM.part_loads)
                    .selectinload(AlphaCasePartLoadORM.moments)
                    .selectinload(AlphaCasePartLoadMomentORM.reference_point),
                )
            )
            return list(session.scalars(stmt).all())

    def get_alpha_case(self, oc_id: int, alpha_deg: float) -> Optional[AlphaCaseORM]:
        with self.get_session() as session:
            stmt = (
                select(AlphaCaseORM)
                .where(
                    AlphaCaseORM.operating_condition_id == oc_id,
                    AlphaCaseORM.alpha_deg == alpha_deg,
                )
                .options(
                    selectinload(AlphaCaseORM.part_loads).selectinload(AlphaCasePartLoadORM.part),
                    selectinload(AlphaCaseORM.part_loads)
                    .selectinload(AlphaCasePartLoadORM.moments)
                    .selectinload(AlphaCasePartLoadMomentORM.reference_point),
                )
            )
            return session.scalar(stmt)

    def set_alpha_case(
        self, oc_id: int, alpha_deg: float, part_loads: list[dict],
        convergence_status: str = "unknown",
    ) -> AlphaCaseORM:
        """Create or replace the α case at (oc_id, alpha_deg) with the given part loads.

        Each entry in part_loads is a dict: {part_id, fx_n, fz_n, moments}, where
        moments maps reference_point_id -> my_nm. An existing case at the same α is
        wiped and rebuilt, so saving is idempotent.
        """
        with self.get_session() as session:
            case = session.scalar(
                select(AlphaCaseORM).where(
                    AlphaCaseORM.operating_condition_id == oc_id,
                    AlphaCaseORM.alpha_deg == alpha_deg,
                )
            )
            if case is None:
                case = AlphaCaseORM(operating_condition_id=oc_id, alpha_deg=alpha_deg)
                session.add(case)
            case.convergence_status = convergence_status
            # Replace the case's loads wholesale (cascade removes their moments).
            for existing in list(case.part_loads):
                session.delete(existing)
            session.flush()
            for entry in part_loads:
                load = AlphaCasePartLoadORM(
                    alpha_case_id=case.id,
                    part_id=entry["part_id"],
                    fx_n=entry.get("fx_n", 0.0),
                    fz_n=entry.get("fz_n", 0.0),
                    my_nm=entry.get("my_nm", 0.0),
                )
                load.moments = [
                    AlphaCasePartLoadMomentORM(reference_point_id=ref_id, my_nm=value)
                    for ref_id, value in entry.get("moments", {}).items()
                ]
                session.add(load)
            session.commit()
            session.refresh(case)
            return case

    def delete_alpha_case(self, alpha_case_id: int) -> bool:
        with self.get_session() as session:
            case = session.get(AlphaCaseORM, alpha_case_id)
            if not case:
                return False
            session.delete(case)
            session.commit()
            return True
