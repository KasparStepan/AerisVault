"""
AerisVault UI - ORM Models
Based on SQLAlchemy 2.0.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class FileType(Enum):
    DRAG_RESULT = "drag_result"
    PROBE_RESULT = "probe_result"
    LOG_FILE = "log_file"
    OTHER = "other"


# Association table for Simulation <-> Tag (Many-to-Many)
simulation_tags = Table(
    "simulation_tags",
    Base.metadata,
    Column("simulation_id", Integer, ForeignKey("simulations.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(20))  # Hex color

    # Relationships
    simulations: Mapped[List["Simulation"]] = relationship(
        secondary=simulation_tags, back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"Tag(id={self.id}, name='{self.name}')"


class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Whether this is an infinite mass (ICFD wind-tunnel) or finite mass (drop test)
    # Infinite mass produces .dat files with force columns (Fpx, Fpy, Fpz, ...)
    # Finite mass produces .csv files with kinematic columns (z_acceleration, z_velocity, ...)
    analysis_type: Mapped[str] = mapped_column(String(20), default="infinite_mass")

    # Physical/Simulation parameters
    velocity: Mapped[Optional[float]] = mapped_column(Float)      # flow velocity (m/s) or initial drop velocity
    ref_area: Mapped[Optional[float]] = mapped_column(Float)      # parachute reference area (m²)
    air_density: Mapped[float] = mapped_column(Float, default=1.225)  # kg/m³
    mass: Mapped[Optional[float]] = mapped_column(Float)           # payload mass (kg), used for F = m·a in finite mass

    # FSI solver & mesh parameters
    time_step_s: Mapped[Optional[float]] = mapped_column(Float)           # FSI time step (s)
    contact_thickness_mm: Mapped[Optional[float]] = mapped_column(Float)  # virtual contact thickness of canopy (mm)
    csd_element_size_mm: Mapped[Optional[float]] = mapped_column(Float)   # CSD mesh element size (mm)
    cfd_element_size_mm: Mapped[Optional[float]] = mapped_column(Float)   # CFD mesh element size (mm)
    wall_clock_time: Mapped[Optional[str]] = mapped_column(String(20))    # how long the solver ran (HH:MM:SS)
    
    # Relationships
    files: Mapped[List["File"]] = relationship(back_populates="simulation", cascade="all, delete-orphan")
    tags: Mapped[List[Tag]] = relationship(secondary=simulation_tags, back_populates="simulations")

    def __repr__(self) -> str:
        return f"Simulation(id={self.id}, name='{self.name}')"


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    simulation_id: Mapped[int] = mapped_column(ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(SQLEnum(FileType), default=FileType.DRAG_RESULT)
    
    storage_format: Mapped[str] = mapped_column(String(20))  # 'dat', 'parquet', etc.
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)  # JSON blob for extra info
    
    # Relationships
    simulation: Mapped["Simulation"] = relationship(back_populates="files")

    def __repr__(self) -> str:
        return f"File(id={self.id}, name='{self.original_filename}', type={self.file_type.value})"
