"""Tests for StorageManager — file storage and conversion."""

import pytest
from pathlib import Path

from aerisvault.core.storage import StorageManager
from aerisvault.core.models import FileType


@pytest.fixture
def storage(tmp_path):
    """Create a StorageManager with a temp directory."""
    return StorageManager(base_dir=str(tmp_path / "data"))


class TestStorageManager:
    def test_init_creates_directories(self, storage):
        assert (storage.base_dir / "raw").is_dir()
        assert (storage.base_dir / "processed").is_dir()

    def test_store_binary_file(self, storage):
        content = b"some binary data"
        path, fmt, size, meta = storage.store_file(
            content, "log.bin", FileType.LOG_FILE, sim_id=1
        )

        assert Path(path).exists()
        assert fmt == "bin"
        assert size == len(content)

    def test_store_dat_file_raw_fallback(self, storage):
        # A .dat file that doesn't parse as valid LS-DYNA output
        # should still be stored as raw
        content = b"not a real dat file\njust garbage"
        path, fmt, size, meta = storage.store_file(
            content, "forces.dat", FileType.DRAG_RESULT, sim_id=2
        )

        assert Path(path).exists()
        assert size == len(content)

    def test_store_creates_sim_subdirectory(self, storage):
        content = b"test"
        storage.store_file(content, "test.txt", FileType.OTHER, sim_id=42)

        sim_dir = storage.base_dir / "raw" / "sim_42"
        assert sim_dir.is_dir()

    def test_delete_file(self, storage):
        content = b"to be deleted"
        path, _, _, _ = storage.store_file(
            content, "temp.dat", FileType.OTHER, sim_id=1
        )

        assert Path(path).exists()
        storage.delete_file(path)
        assert not Path(path).exists()

    def test_delete_nonexistent_no_error(self, storage):
        # Should not raise
        storage.delete_file("/nonexistent/path/file.dat")
