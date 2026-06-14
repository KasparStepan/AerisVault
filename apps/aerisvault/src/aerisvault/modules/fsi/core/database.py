"""
AerisVault UI - Database Manager
Handles SQLite operations using SQLAlchemy.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.orm import Session, selectinload, sessionmaker

from .models import Base, File, FileType, Simulation, Tag

logger = logging.getLogger(__name__)


class SimulationDatabase:
    """Manager for simulation metadata database."""

    def __init__(self, db_url: str = "sqlite:///aerisvault.db"):
        self.engine = create_engine(db_url)
        # expire_on_commit=False keeps attributes accessible after session closes.
        # Without this, accessing sim.tags or sim.files outside the session raises
        # DetachedInstanceError, which breaks Streamlit's rendering.
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    # --- Simulation Operations ---

    def create_simulation(self, name: str, description: str = "") -> Simulation:
        with self.get_session() as session:
            sim = Simulation(name=name, description=description)
            session.add(sim)
            session.commit()
            session.refresh(sim)
            return sim

    def get_simulation(self, sim_id: int) -> Optional[Simulation]:
        with self.get_session() as session:
            stmt = (
                select(Simulation)
                .where(Simulation.id == sim_id)
                .options(selectinload(Simulation.tags), selectinload(Simulation.files))
            )
            return session.scalar(stmt)

    def list_simulations(self) -> List[Simulation]:
        with self.get_session() as session:
            stmt = (
                select(Simulation)
                .order_by(Simulation.created_at.desc())
                .options(selectinload(Simulation.tags), selectinload(Simulation.files))
            )
            return list(session.scalars(stmt).all())

    def update_simulation(self, sim_id: int, **kwargs) -> bool:
        with self.get_session() as session:
            stmt = update(Simulation).where(Simulation.id == sim_id).values(**kwargs)
            result = session.execute(stmt)
            session.commit()
            return result.rowcount > 0

    def delete_simulation(self, sim_id: int) -> bool:
        with self.get_session() as session:
            sim = session.get(Simulation, sim_id)
            if sim:
                session.delete(sim)
                session.commit()
                return True
            return False

    # --- File Operations ---

    def create_file(
        self,
        simulation_id: int,
        filename: str,
        storage_path: str,
        file_type: FileType = FileType.DRAG_RESULT,
        storage_format: str = "dat",
        size_bytes: int = 0,
        metadata_json: Optional[str] = None,
    ) -> File:
        with self.get_session() as session:
            file_obj = File(
                simulation_id=simulation_id,
                original_filename=filename,
                file_type=file_type,
                storage_format=storage_format,
                storage_path=storage_path,
                file_size_bytes=size_bytes,
                metadata_json=metadata_json,
            )
            session.add(file_obj)
            session.commit()
            session.refresh(file_obj)
            return file_obj

    def get_files_by_simulation(self, sim_id: int) -> List[File]:
        with self.get_session() as session:
            stmt = select(File).where(File.simulation_id == sim_id)
            return list(session.scalars(stmt).all())

    def delete_file(self, file_id: int) -> bool:
        with self.get_session() as session:
            file_obj = session.get(File, file_id)
            if file_obj:
                session.delete(file_obj)
                session.commit()
                return True
            return False

    # --- Tag Operations ---

    def create_tag(self, name: str, color: Optional[str] = None) -> Tag:
        with self.get_session() as session:
            tag = Tag(name=name, color=color)
            session.add(tag)
            session.commit()
            session.refresh(tag)
            return tag

    def list_all_tags(self) -> List[Tag]:
        with self.get_session() as session:
            return list(session.scalars(select(Tag)).all())

    def add_tags_to_simulation(self, sim_id: int, tag_names: List[str]):
        with self.get_session() as session:
            sim = session.get(Simulation, sim_id)
            if not sim:
                return
            
            for name in tag_names:
                tag_stmt = select(Tag).where(Tag.name == name)
                tag = session.scalar(tag_stmt)
                if tag and tag not in sim.tags:
                    sim.tags.append(tag)
            
            session.commit()
    
    def remove_tag_from_simulation(self, sim_id: int, tag_name: str):
        """Remove a specific tag from a simulation (tag itself is kept)."""
        with self.get_session() as session:
            sim = session.get(Simulation, sim_id)
            if not sim:
                return
            sim.tags = [t for t in sim.tags if t.name != tag_name]
            session.commit()

    def delete_tag(self, tag_id: int):
        with self.get_session() as session:
            tag = session.get(Tag, tag_id)
            if tag:
                session.delete(tag)
                session.commit()
