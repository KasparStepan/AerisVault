"""Base simulation class for all LS-DYNA simulation types."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class SimulationMetadata:
    """Structured metadata extracted from simulation directory names.

    Attributes:
        parachute_type: Type of parachute (e.g., 'cross', 'scrab').
        size: Characteristic dimension (e.g., '2m').
        raw: Original key-value pairs from parsing.
    """
    parachute_type: str = ""
    size: str = ""
    raw: Dict[str, str] = field(default_factory=dict)


class BaseSimulation:
    """Base class for any LS-DYNA simulation result set.

    Validates the directory exists and provides common metadata storage.

    Args:
        directory_path: Path to the simulation results directory.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """

    def __init__(self, directory_path: str | Path) -> None:
        self.dir_path = Path(directory_path).resolve()
        if not self.dir_path.exists() or not self.dir_path.is_dir():
            raise FileNotFoundError(
                f"Simulation directory not found: {self.dir_path}"
            )

        self.metadata = SimulationMetadata()

    def summary(self) -> str:
        """Returns a human-readable summary of the simulation."""
        meta_str = ", ".join(
            f"{k}={v}" for k, v in self.metadata.raw.items()
        )
        return f"<{self.__class__.__name__}: {self.dir_path.name} | {meta_str}>"

    def __repr__(self) -> str:
        return self.summary()
