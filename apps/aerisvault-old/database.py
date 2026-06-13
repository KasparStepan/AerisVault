"""
AerisVault - Database Manager
Handles all database interactions using SQLAlchemy.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pathlib import Path
import sqlalchemy
from sqlalchemy import create_engine, select, update, delete
from sqlalchemy.orm import sessionmaker, Session, joinedload

from .models import Base, Simulation, File, Tag, FileType, StorageFormat
from .config import get_settings

class SimulationDatabase:
    """
    Manages database connections and CRUD operations.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            settings = get_settings()
            # Ensure directory exists
            settings.data_dir.mkdir(parents=True, exist_ok=True)
            db_path = f"sqlite:///{settings.data_dir}/aerisvault.db"
            
        self.engine = create_engine(db_path, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize tables
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    # --- Simulation Operations ---

    def create_simulation(self, name: str, description: str = "") -> Simulation:
        """Create a new simulation entry."""
        session = self.get_session()
        try:
            sim = Simulation(name=name, description=description)
            session.add(sim)
            session.commit()
            session.refresh(sim)
            return sim
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_simulation(self, sim_id: int) -> Optional[Simulation]:
        """Get simulation by ID."""
        session = self.get_session()
        try:
            return session.get(Simulation, sim_id)
        finally:
            session.close()
            
    def get_simulation_by_name(self, name: str) -> Optional[Simulation]:
        """Get simulation by unique name."""
        session = self.get_session()
        try:
            stmt = select(Simulation).where(Simulation.name == name)
            result = session.execute(stmt).scalar_one_or_none()
            return result
        finally:
            session.close()

    def list_simulations(self, order_by: str = "created_at") -> List[Simulation]:
        """List all simulations."""
        session = self.get_session()
        try:
            stmt = select(Simulation).options(joinedload(Simulation.tags))
            if order_by == "created_at":
                stmt = stmt.order_by(Simulation.created_at.desc())
            elif order_by == "name":
                stmt = stmt.order_by(Simulation.name)
            
            return session.execute(stmt).unique().scalars().all()
        finally:
            session.close()

    def update_simulation(self, sim_id: int, **kwargs) -> Optional[Simulation]:
        """Update simulation fields."""
        session = self.get_session()
        try:
            stmt = update(Simulation).where(Simulation.id == sim_id).values(**kwargs)
            session.execute(stmt)
            session.commit()
            return session.get(Simulation, sim_id)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_simulation(self, sim_id: int) -> bool:
        """Delete a simulation and its associated files."""
        session = self.get_session()
        try:
            sim = session.get(Simulation, sim_id)
            if sim:
                session.delete(sim)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # --- File Operations ---

    def create_file(self, 
                   simulation_id: int, 
                   filename: str, 
                   file_type: FileType, 
                   storage_format: StorageFormat,
                   storage_path: str,
                   size_bytes: int,
                   metadata_json: Optional[str] = None) -> File:
        """Attach a file to a simulation."""
        session = self.get_session()
        try:
            file_entry = File(
                simulation_id=simulation_id,
                original_filename=filename,
                file_type=file_type,
                storage_format=storage_format,
                storage_path=storage_path,
                file_size_bytes=size_bytes,
                metadata_json=metadata_json
            )
            session.add(file_entry)
            session.commit()
            session.refresh(file_entry)
            return file_entry
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_files_by_simulation(self, simulation_id: int) -> List[File]:
        """Get all files for a simulation."""
        session = self.get_session()
        try:
            stmt = select(File).where(File.simulation_id == simulation_id)
            return session.execute(stmt).scalars().all()
        finally:
            session.close()
            
    def delete_file(self, file_id: int) -> bool:
        """Delete a file record (does not delete physical file)."""
        session = self.get_session()
        try:
            file_obj = session.get(File, file_id)
            if file_obj:
                session.delete(file_obj)
                session.commit()
                return True
            return False
        finally:
            session.close()

    # --- Tag Operations ---

    def create_tag(self, name: str, color: Optional[str] = None) -> Tag:
        """Create a new tag."""
        session = self.get_session()
        try:
            tag = Tag(name=name, color=color)
            session.add(tag)
            session.commit()
            session.refresh(tag)
            return tag
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def list_all_tags(self) -> List[Tag]:
        """List all available tags."""
        session = self.get_session()
        try:
            stmt = select(Tag).options(joinedload(Tag.simulations))
            return session.execute(stmt).unique().scalars().all()
        finally:
            session.close()
            
    def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag."""
        session = self.get_session()
        try:
            tag = session.get(Tag, tag_id)
            if tag:
                session.delete(tag)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def add_tags_to_simulation(self, simulation_id: int, tag_names: List[str]):
        """Associate tags with a simulation, creating them if they don't exist."""
        session = self.get_session()
        try:
            sim = session.get(Simulation, simulation_id)
            if not sim:
                raise ValueError(f"Simulation {simulation_id} not found")

            for name in tag_names:
                # Check if tag exists
                stmt = select(Tag).where(Tag.name == name)
                tag = session.execute(stmt).scalar_one_or_none()
                
                if not tag:
                    tag = Tag(name=name)
                    session.add(tag)
                
                if tag not in sim.tags:
                    sim.tags.append(tag)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

# Alias for backward compatibility if needed
DatabaseManager = SimulationDatabase