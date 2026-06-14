"""
AerisVault UI - Configuration Management
Handles application settings and persistence.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FilterSettings:
    enabled_by_default: bool = True
    default_filter_type: str = "cfc"  # cfc, moving_average, butterworth, savgol
    cfc_class: int = 60
    moving_avg_window: int = 5
    lowpass_cutoff_freq: float = 60.0
    savgol_window_length: int = 51
    savgol_polyorder: int = 3


@dataclass
class PlotSettings:
    theme: str = "plotly_white"
    width: int = 800
    height: int = 500
    line_width: int = 2
    font_size: int = 12
    show_grid: bool = True


@dataclass
class AppSettings:
    data_dir: str = "data"
    db_name: str = "aerisvault.db"
    max_file_size_mb: int = 50
    filter_settings: FilterSettings = field(default_factory=FilterSettings)
    plot_settings: PlotSettings = field(default_factory=PlotSettings)
    config_path: str = "config.json"

    def save(self):
        """Save settings to JSON file."""
        with open(self.config_path, "w") as f:
            json.dump(asdict(self), f, indent=4)

    @classmethod
    def load(cls, path: str = "config.json") -> "AppSettings":
        """Load settings from JSON file."""
        if not os.path.exists(path):
            return cls(config_path=path)
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
                
            # Manually reconstruct nested dataclasses
            f_data = data.pop("filter_settings", {})
            p_data = data.pop("plot_settings", {})
            data.pop("config_path", None)  # replaced by the actual path arg

            settings = cls(**data, config_path=path)
            settings.filter_settings = FilterSettings(**f_data)
            settings.plot_settings = PlotSettings(**p_data)
            return settings
        except Exception:
            return cls(config_path=path)


# Global settings instance
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        # Default location in monorepo apps/aerisvault-ui/
        _settings = AppSettings.load()
    return _settings
