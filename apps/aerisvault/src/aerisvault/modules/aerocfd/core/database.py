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
    AircraftORM, AlphaCaseORM, Base, OperatingConditionORM,
)

logger = logging.getLogger(__name__)


class AeroCfdDatabase:
    """Manager for the aerocfd aircraft/operating-condition/alpha-case database."""

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
            session.add(aircraft)
            session.commit()
            session.refresh(aircraft)
            return aircraft

    def list_aircraft(self) -> List[AircraftORM]:
        with self.get_session() as session:
            stmt = (
                select(AircraftORM)
                .order_by(AircraftORM.created_at.desc())
                .options(selectinload(AircraftORM.operating_conditions))
            )
            return list(session.scalars(stmt).all())

    def get_aircraft(self, aircraft_id: int) -> Optional[AircraftORM]:
        with self.get_session() as session:
            stmt = (
                select(AircraftORM)
                .where(AircraftORM.id == aircraft_id)
                .options(selectinload(AircraftORM.operating_conditions))
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

    def update_operating_condition(self, oc_id: int, **fields) -> bool:
        with self.get_session() as session:
            oc = session.get(OperatingConditionORM, oc_id)
            if not oc:
                return False
            for key, value in fields.items():
                setattr(oc, key, value)
            session.commit()
            return True

    def delete_operating_condition(self, oc_id: int) -> bool:
        with self.get_session() as session:
            oc = session.get(OperatingConditionORM, oc_id)
            if not oc:
                return False
            session.delete(oc)
            session.commit()
            return True

    # --- Alpha cases ---

    def list_alpha_cases(self, oc_id: int) -> List[AlphaCaseORM]:
        with self.get_session() as session:
            stmt = (
                select(AlphaCaseORM)
                .where(AlphaCaseORM.operating_condition_id == oc_id)
                .order_by(AlphaCaseORM.alpha_deg)
            )
            return list(session.scalars(stmt).all())

    def replace_alpha_cases(self, oc_id: int, rows: list[dict]) -> int:
        """Replace all α cases for an operating condition with the given rows.

        Each row is a dict with keys: alpha_deg, fx_n, fz_n, my_nm, and optionally
        convergence_status / case_name / notes. The data-entry page edits the whole
        table at once, so a wholesale replace is the simplest faithful save.
        """
        with self.get_session() as session:
            existing = session.scalars(
                select(AlphaCaseORM).where(AlphaCaseORM.operating_condition_id == oc_id)
            ).all()
            for case in existing:
                session.delete(case)
            for row in rows:
                session.add(AlphaCaseORM(
                    operating_condition_id=oc_id,
                    alpha_deg=row["alpha_deg"],
                    fx_n=row["fx_n"],
                    fz_n=row["fz_n"],
                    my_nm=row["my_nm"],
                    convergence_status=row.get("convergence_status", "unknown"),
                    case_name=row.get("case_name"),
                    notes=row.get("notes"),
                ))
            session.commit()
            return len(rows)
