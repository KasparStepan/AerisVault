"""
AerisVault - Database Models
Database models for AerisVault using SQLAlchemy ORM.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Float, Enum as SQLEnum, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# Association table for many-to-many relationship between Simulations and Tags
simulation_tags = Table(
    'simulation_tags',
    Base.metadata,
    Column('simulation_id', Integer, ForeignKey('simulations.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class FileType(enum.Enum):
    """Enumeration of supported file types."""
    KEYWORD = "keyword"
    DRAG_RESULT = "drag_result"
    THERMAL_RESULT = "thermal_result"
    DISPLACEMENT_RESULT = "displacement_result"
    GENERIC = "generic"


class StorageFormat(enum.Enum):
    """How the file data is stored."""
    PARQUET = "parquet"
    GZIP = "gzip"
    RAW = "raw"


class Tag(Base):
    __tablename__ = "tags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    simulations: Mapped[List["Simulation"]] = relationship(
        "Simulation",
        secondary=simulation_tags,
        back_populates="tags"
    )


class Simulation(Base):
    __tablename__ = "simulations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # --- Engineering Parameters ---
    velocity: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="Free stream velocity [m/s]")
    ref_area: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="Reference area S [m^2]")
    air_density: Mapped[Optional[float]] = mapped_column(Float, default=1.225, nullable=True, comment="Air density [kg/m^3]")
    
    files: Mapped[List["File"]] = relationship(
        "File", 
        back_populates="simulation",
        cascade="all, delete-orphan"
    )
    
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=simulation_tags,
        back_populates="simulations"
    )


class File(Base):
    __tablename__ = "files"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    simulation_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("simulations.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[FileType] = mapped_column(SQLEnum(FileType), nullable=False)
    storage_format: Mapped[StorageFormat] = mapped_column(SQLEnum(StorageFormat), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="files")