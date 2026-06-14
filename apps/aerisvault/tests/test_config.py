"""Tests for AppSettings configuration."""

import json
import pytest
from pathlib import Path

from aerisvault.modules.fsi.core.config import AppSettings, FilterSettings, PlotSettings


@pytest.fixture
def tmp_config(tmp_path):
    """Return a path for a temporary config file."""
    return str(tmp_path / "config.json")


class TestAppSettings:
    def test_defaults(self):
        settings = AppSettings()
        assert settings.data_dir == "data"
        assert settings.db_name == "aerisvault.db"
        assert settings.max_file_size_mb == 50

    def test_filter_defaults(self):
        settings = AppSettings()
        f = settings.filter_settings
        assert f.default_filter_type == "cfc"
        assert f.cfc_class == 60
        assert f.enabled_by_default is True

    def test_plot_defaults(self):
        settings = AppSettings()
        p = settings.plot_settings
        assert p.theme == "plotly_white"
        assert p.width == 800

    def test_save_and_load(self, tmp_config):
        original = AppSettings(config_path=tmp_config)
        original.filter_settings.cfc_class = 180
        original.data_dir = "/custom/path"
        original.save()

        loaded = AppSettings.load(tmp_config)
        assert loaded.data_dir == "/custom/path"
        assert loaded.filter_settings.cfc_class == 180

    def test_load_missing_file_returns_defaults(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        settings = AppSettings.load(path)
        assert settings.data_dir == "data"

    def test_load_corrupted_file_returns_defaults(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not valid json {{{")
        settings = AppSettings.load(str(path))
        assert settings.data_dir == "data"

    def test_save_creates_valid_json(self, tmp_config):
        settings = AppSettings(config_path=tmp_config)
        settings.save()

        with open(tmp_config) as f:
            data = json.load(f)

        assert "filter_settings" in data
        assert "plot_settings" in data
        assert data["db_name"] == "aerisvault.db"
