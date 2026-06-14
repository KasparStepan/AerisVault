"""aerocfd module — SQLAlchemy ORM (SQLAlchemy 2.0).

The hierarchy is Aircraft → OperatingCondition → AlphaCase. These ORM rows are
the storage layer only; the pure library dataclasses in `aerocfd.models` are the
computation contract. `mappers.py` translates between the two.

Slice-2 schema (see spec §8.3). All forces/moments are raw body-frame totals
exactly as Fluent reports them — the library does the rotation and sign flip.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AircraftORM(Base):
    __tablename__ = "aircraft"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Reference values (SI). Editing these after polars are computed is the
    # mutable-state hazard the UI warns about (spec §8.6).
    s_ref_m2: Mapped[float] = mapped_column(Float, nullable=False)
    c_ref_m: Mapped[float] = mapped_column(Float, nullable=False)
    b_ref_m: Mapped[float] = mapped_column(Float, nullable=False)
    axis_convention: Mapped[str] = mapped_column(String(32), default="x_fwd_z_up_rh")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    operating_conditions: Mapped[List["OperatingConditionORM"]] = relationship(
        back_populates="aircraft", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"AircraftORM(id={self.id}, name='{self.name}')"


class OperatingConditionORM(Base):
    __tablename__ = "operating_condition"

    id: Mapped[int] = mapped_column(primary_key=True)
    aircraft_id: Mapped[int] = mapped_column(
        ForeignKey("aircraft.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    velocity_mps: Mapped[float] = mapped_column(Float, nullable=False)
    density_kgpm3: Mapped[float] = mapped_column(Float, nullable=False)

    # Optional free-stream / turbulence metadata — stored for the record, not
    # used by the slice-2 coefficient math.
    pressure_pa: Mapped[Optional[float]] = mapped_column(Float)
    altitude_m: Mapped[Optional[float]] = mapped_column(Float)
    turbulence_model: Mapped[Optional[str]] = mapped_column(String(64))
    turbulence_bc_method: Mapped[Optional[str]] = mapped_column(String(64))
    turbulence_intensity_pct: Mapped[Optional[float]] = mapped_column(Float)
    turbulent_viscosity_ratio: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    aircraft: Mapped["AircraftORM"] = relationship(back_populates="operating_conditions")
    alpha_cases: Mapped[List["AlphaCaseORM"]] = relationship(
        back_populates="operating_condition", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"OperatingConditionORM(id={self.id}, name='{self.name}')"


class AlphaCaseORM(Base):
    __tablename__ = "alpha_case"

    id: Mapped[int] = mapped_column(primary_key=True)
    operating_condition_id: Mapped[int] = mapped_column(
        ForeignKey("operating_condition.id", ondelete="CASCADE"), nullable=False
    )
    alpha_deg: Mapped[float] = mapped_column(Float, nullable=False)
    case_name: Mapped[Optional[str]] = mapped_column(String(255))
    # convergence_status is a library ConvergenceStatus stored as its TEXT value.
    convergence_status: Mapped[str] = mapped_column(String(32), default="unknown")
    iteration_count: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Raw Fluent body-frame totals (Fx forward-positive; My raw, sign flip in lib).
    fx_n: Mapped[float] = mapped_column(Float, nullable=False)
    fz_n: Mapped[float] = mapped_column(Float, nullable=False)
    my_nm: Mapped[float] = mapped_column(Float, nullable=False)

    operating_condition: Mapped["OperatingConditionORM"] = relationship(
        back_populates="alpha_cases"
    )

    def __repr__(self) -> str:
        return f"AlphaCaseORM(id={self.id}, alpha_deg={self.alpha_deg})"
