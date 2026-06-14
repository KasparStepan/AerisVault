"""Tests for per-module data directory resolution."""

from aerisvault.shared import paths


def test_data_dir_for_appends_key(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "DATA_ROOT", tmp_path)
    result = paths.data_dir_for("fsi")
    assert result == tmp_path / "fsi"


def test_data_dir_for_creates_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "DATA_ROOT", tmp_path)
    result = paths.data_dir_for("aerocfd")
    assert result.exists()
    assert result.is_dir()


def test_data_root_is_repo_data_dir():
    """DATA_ROOT must resolve to <repo>/data, not apps/data — guards the parents[] index.

    Identifies the repo root by its marker directories (apps/ and libs/) rather
    than a hardcoded folder name, so a clone into any directory still passes.
    """
    assert paths.DATA_ROOT.name == "data"
    repo_root = paths.DATA_ROOT.parent
    assert (repo_root / "apps").is_dir()
    assert (repo_root / "libs").is_dir()
