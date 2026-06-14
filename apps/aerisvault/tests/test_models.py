"""Tests for ORM models — Simulation, File, Tag."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from aerisvault.core.models import Base, File, FileType, Simulation, Tag, simulation_tags


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestSimulation:
    def test_create_simulation(self, db_session):
        sim = Simulation(name="cross_2m_6ms", description="Test run")
        db_session.add(sim)
        db_session.commit()

        assert sim.id is not None
        assert sim.name == "cross_2m_6ms"
        assert sim.air_density == 1.225  # default

    def test_simulation_with_physics(self, db_session):
        sim = Simulation(name="test", velocity=6.0, ref_area=3.14)
        db_session.add(sim)
        db_session.commit()

        assert sim.velocity == 6.0
        assert sim.ref_area == 3.14

    def test_simulation_repr(self, db_session):
        sim = Simulation(name="my_sim")
        db_session.add(sim)
        db_session.commit()

        assert "my_sim" in repr(sim)


class TestFile:
    def test_create_file(self, db_session):
        sim = Simulation(name="parent_sim")
        db_session.add(sim)
        db_session.commit()

        f = File(
            simulation_id=sim.id,
            original_filename="drag_forces.dat",
            file_type=FileType.DRAG_RESULT,
            storage_format="dat",
            storage_path="/data/raw/sim_1/drag_forces.dat",
            file_size_bytes=1024,
        )
        db_session.add(f)
        db_session.commit()

        assert f.id is not None
        assert f.simulation_id == sim.id
        assert f.file_type == FileType.DRAG_RESULT

    def test_cascade_delete(self, db_session):
        """Deleting a simulation should delete its files."""
        sim = Simulation(name="to_delete")
        db_session.add(sim)
        db_session.commit()

        f = File(
            simulation_id=sim.id,
            original_filename="test.dat",
            storage_format="dat",
            storage_path="/tmp/test.dat",
            file_size_bytes=100,
        )
        db_session.add(f)
        db_session.commit()
        file_id = f.id

        db_session.delete(sim)
        db_session.commit()

        assert db_session.get(File, file_id) is None

    def test_file_types(self):
        assert FileType.DRAG_RESULT.value == "drag_result"
        assert FileType.PROBE_RESULT.value == "probe_result"
        assert FileType.LOG_FILE.value == "log_file"
        assert FileType.OTHER.value == "other"


class TestTag:
    def test_create_tag(self, db_session):
        tag = Tag(name="convergence", color="#ff0000")
        db_session.add(tag)
        db_session.commit()

        assert tag.id is not None
        assert tag.name == "convergence"

    def test_tag_simulation_relationship(self, db_session):
        sim = Simulation(name="tagged_sim")
        tag = Tag(name="mesh_study")
        sim.tags.append(tag)
        db_session.add(sim)
        db_session.commit()

        assert len(sim.tags) == 1
        assert sim.tags[0].name == "mesh_study"
        assert len(tag.simulations) == 1

    def test_unique_tag_name(self, db_session):
        db_session.add(Tag(name="unique"))
        db_session.commit()

        from sqlalchemy.exc import IntegrityError
        db_session.add(Tag(name="unique"))
        with pytest.raises(IntegrityError):
            db_session.commit()
