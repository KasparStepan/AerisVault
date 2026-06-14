"""Infinite Mass simulation model — wind-tunnel / ICFD drag analysis.

Automatically locates and parses ``.dat`` files containing ICFD
pressure and viscous force/moment histories.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from dynaprocessing.io.lsdyna_csv import parse_infinite_mass_dat
from dynaprocessing.io.metadata import (
    InfiniteMassMetadata,
    parse_infinite_mass_directory,
)
from dynaprocessing.models.curve import Curve
from dynaprocessing.models.simulation import BaseSimulation

logger = logging.getLogger(__name__)


class InfiniteMassSimulation(BaseSimulation):
    """Represents an Infinite Mass (ICFD) simulation run.

    On construction, the class:
    1. Validates the directory exists.
    2. Tries to parse metadata from the directory name.
    3. Loads curve data from the first valid ``.dat`` file found.

    Args:
        directory_path: Path to the simulation results directory.
        invert_z: Whether to invert Z-direction forces for standard
            engineering sign convention (default True).
    """

    def __init__(
        self, directory_path: str | Path, *, invert_z: bool = True
    ) -> None:
        super().__init__(directory_path)

        # Parse metadata (non-fatal)
        self.sim_metadata: Optional[InfiniteMassMetadata] = None
        try:
            self.sim_metadata = parse_infinite_mass_directory(self.dir_path)
            self.metadata.parachute_type = self.sim_metadata.parachute_type
            self.metadata.size = self.sim_metadata.size
            self.metadata.raw = {
                "flow_velocity": self.sim_metadata.flow_velocity,
                "simulation_type": self.sim_metadata.simulation_type,
                "parachute_type": self.sim_metadata.parachute_type,
                "size": self.sim_metadata.size,
            }
        except ValueError as exc:
            logger.warning("Could not parse metadata: %s", exc)

        self.curves: Dict[str, Curve] = {}
        self._load_data(invert_z=invert_z)

    def _load_data(self, *, invert_z: bool) -> None:
        """Locate and parse .dat files in the simulation directory."""
        dat_files = sorted(self.dir_path.glob("*.dat"))

        for dat_file in dat_files:
            parsed_curves = parse_infinite_mass_dat(
                dat_file, invert_z=invert_z
            )
            if parsed_curves:
                self.curves = {c.name: c for c in parsed_curves}
                return

        logger.warning("No valid .dat file found in %s", self.dir_path)

    def get_curve(self, curve_name: str) -> Optional[Curve]:
        """Retrieve a curve by its column name (e.g., 'Fpz').

        Args:
            curve_name: Column name from the .dat file.
        """
        return self.curves.get(curve_name)

    def list_curves(self) -> List[Curve]:
        """All loaded curves (flat storage, one Curve per force/moment column)."""
        return list(self.curves.values())

    # ------------------------------------------------------------------
    # Convenience properties for common ICFD force columns
    # ------------------------------------------------------------------
    @property
    def fpx(self) -> Optional[Curve]:
        """X-direction pressure force."""
        return self.get_curve("Fpx")

    @property
    def fpy(self) -> Optional[Curve]:
        """Y-direction pressure force."""
        return self.get_curve("Fpy")

    @property
    def fpz(self) -> Optional[Curve]:
        """Z-direction pressure force."""
        return self.get_curve("Fpz")

    @property
    def label(self) -> str:
        """Human-readable label for plot legends and reports."""
        if self.sim_metadata:
            return self.sim_metadata.label
        return self.dir_path.name
