"""
AerisVault - Configuration Management
"""

from pathlib import Path
from typing import Optional
import json
from dataclasses import dataclass, asdict

@dataclass
class FilterSettings:
    enabled_by_default: bool = False
    default_filter_type: str = "savgol"
    savgol_window_length: int = 51
    savgol_polyorder: int = 3
    moving_avg_window: int = 10
    lowpass_cutoff_freq: float = 10.0
    lowpass_order: int = 4

@dataclass
class PlotSettings:
    theme: str = "plotly_white"
    width: int = 1200
    height: int = 600
    line_width: int = 2
    original_line_style: str = "dash"
    filtered_line_style: str = "solid"
    original_line_opacity: float = 0.5
    show_grid: bool = True
    font_size: int = 12

class AppSettings:
    """Application settings container."""
    data_dir: Path
    max_file_size_mb: int
    filter_settings: FilterSettings
    plot_settings: PlotSettings
    
    def __init__(self, data_dir: Optional[Path] = None, **kwargs):
        if isinstance(data_dir, str):
            data_dir = Path(data_dir)
        # Default to project's data folder (relative to this config file)
        default_data_dir = Path(__file__).parent.parent.parent / "data"
        self.data_dir = data_dir or default_data_dir
        self.max_file_size_mb = kwargs.get('max_file_size_mb', 100)
        self.filter_settings = FilterSettings(**kwargs.get('filter_settings', {}))
        self.plot_settings = PlotSettings(**kwargs.get('plot_settings', {}))
    
    def to_dict(self) -> dict:
        return {
            'data_dir': str(self.data_dir),
            'max_file_size_mb': self.max_file_size_mb,
            'filter_settings': asdict(self.filter_settings),
            'plot_settings': asdict(self.plot_settings)
        }
    
    def save(self):
        config_path = self.data_dir / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls) -> 'AppSettings':
        default_dir = Path.home() / ".aerisvault" / "data"
        config_path = default_dir / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return cls(**json.load(f))
            except Exception:
                pass
        return cls()

_settings: Optional[AppSettings] = None

def get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        _settings = AppSettings.load()
    return _settings