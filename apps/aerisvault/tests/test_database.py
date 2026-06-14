"""Tests for SimulationDatabase manager."""

import pytest
from aerisvault.modules.fsi.core.database import SimulationDatabase
from aerisvault.modules.fsi.core.models import FileType


@pytest.fixture
def db():
    """Create an in-memory database manager for each test."""
    return SimulationDatabase("sqlite:///:memory:")


class TestSimulationCRUD:
    def test_create_and_list(self, db):
        db.create_simulation("sim_01", "First run")
        db.create_simulation("sim_02", "Second run")

        sims = db.list_simulations()
        assert len(sims) == 2

    def test_get_simulation(self, db):
        created = db.create_simulation("test_sim")
        fetched = db.get_simulation(created.id)

        assert fetched is not None
        assert fetched.name == "test_sim"

    def test_update_simulation(self, db):
        sim = db.create_simulation("old_name")
        db.update_simulation(sim.id, name="new_name", velocity=8.0)

        updated = db.get_simulation(sim.id)
        assert updated.name == "new_name"
        assert updated.velocity == 8.0

    def test_delete_simulation(self, db):
        sim = db.create_simulation("to_delete")
        assert db.delete_simulation(sim.id) is True
        assert db.get_simulation(sim.id) is None

    def test_delete_nonexistent(self, db):
        assert db.delete_simulation(999) is False

    def test_list_order_newest_first(self, db):
        db.create_simulation("first")
        db.create_simulation("second")
        sims = db.list_simulations()
        # Most recent first
        assert sims[0].name == "second"


class TestFileCRUD:
    def test_create_and_list_files(self, db):
        sim = db.create_simulation("parent")
        db.create_file(
            simulation_id=sim.id,
            filename="forces.dat",
            storage_path="/data/forces.dat",
            file_type=FileType.DRAG_RESULT,
            storage_format="dat",
            size_bytes=2048,
        )

        files = db.get_files_by_simulation(sim.id)
        assert len(files) == 1
        assert files[0].original_filename == "forces.dat"

    def test_delete_file(self, db):
        sim = db.create_simulation("parent")
        f = db.create_file(sim.id, "test.dat", "/tmp/test.dat")
        assert db.delete_file(f.id) is True
        assert db.get_files_by_simulation(sim.id) == []

    def test_delete_nonexistent_file(self, db):
        assert db.delete_file(999) is False


class TestTagCRUD:
    def test_create_and_list_tags(self, db):
        db.create_tag("mesh_study", "#ff0000")
        db.create_tag("validated", "#00ff00")

        tags = db.list_all_tags()
        assert len(tags) == 2

    def test_add_tags_to_simulation(self, db):
        sim = db.create_simulation("tagged")
        db.create_tag("important")
        db.add_tags_to_simulation(sim.id, ["important"])

        # Verify via a fresh session query
        fetched = db.get_simulation(sim.id)
        assert len(fetched.tags) == 1
        assert fetched.tags[0].name == "important"

    def test_add_nonexistent_tag_ignored(self, db):
        sim = db.create_simulation("test")
        # Should not raise — just silently skip
        db.add_tags_to_simulation(sim.id, ["nonexistent"])

    def test_delete_tag(self, db):
        tag = db.create_tag("temp")
        db.delete_tag(tag.id)
        assert db.list_all_tags() == []
