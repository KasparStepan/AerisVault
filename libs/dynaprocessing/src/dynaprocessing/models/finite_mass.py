"""Finite Mass simulation model — drop-test analysis.

Automatically locates and parses ``All_data.csv`` or ``Accel.csv``
in the simulation results directory.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from dynaprocessing.io.lsdyna_csv import parse_lsdyna_csv
from dynaprocessing.io.metadata import (
    FiniteMassMetadata,
    parse_finite_mass_directory,
)
from dynaprocessing.models.curve import Curve
from dynaprocessing.models.simulation import BaseSimulation

logger = logging.getLogger(__name__)


class FiniteMassSimulation(BaseSimulation):
    """Represents a Finite Mass (drop-test) simulation run.

    On construction, the class:
    1. Validates the directory exists.
    2. Tries to parse metadata from the directory name.
    3. Loads curve data from ``All_data.csv`` or ``Accel.csv``.

    Args:
        directory_path: Path to the simulation results directory.
    """

    def __init__(self, directory_path: str | Path) -> None:
        super().__init__(directory_path)

        # Parse metadata (non-fatal if directory naming is non-standard)
        self.sim_metadata: Optional[FiniteMassMetadata] = None
        try:
            self.sim_metadata = parse_finite_mass_directory(self.dir_path)
            self.metadata.parachute_type = self.sim_metadata.parachute_type
            self.metadata.size = self.sim_metadata.size
            self.metadata.raw = {
                "mass": self.sim_metadata.mass,
                "initial_velocity": self.sim_metadata.initial_velocity,
                "parachute_type": self.sim_metadata.parachute_type,
                "size": self.sim_metadata.size,
            }
        except ValueError as exc:
            logger.warning("Could not parse metadata: %s", exc)

        # {node_id: {curve_name: Curve}}
        self.curves: Dict[str, Dict[str, Curve]] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load curve data from CSV files in the simulation directory."""
        all_data_path = self.dir_path / "All_data.csv"
        accel_path = self.dir_path / "Accel.csv"

        if all_data_path.exists():
            self.curves = parse_lsdyna_csv(all_data_path)
        elif accel_path.exists():
            self.curves = parse_lsdyna_csv(accel_path)
        else:
            logger.warning(
                "No All_data.csv or Accel.csv found in %s", self.dir_path
            )

    def get_curve(
        self, curve_name: str, node_id: Optional[str] = None
    ) -> Optional[Curve]:
        """Retrieve a specific curve by name (and optionally node ID).

        If *node_id* is omitted, returns the first matching curve
        across all nodes.

        Args:
            curve_name: Physical quantity name (e.g., 'z_acceleration').
            node_id: Optional LS-DYNA node ID filter.

        Returns:
            The matching Curve, or None if not found.
        """
        for n_id, node_curves in self.curves.items():
            if node_id and n_id != node_id:
                continue
            if curve_name in node_curves:
                return node_curves[curve_name]
        return None

    def get_all_curves_by_name(self, curve_name: str) -> List[Curve]:
        """Return all curves matching a name (e.g., from multiple nodes).

        Args:
            curve_name: Physical quantity name to search for.
        """
        return [
            node_curves[curve_name]
            for node_curves in self.curves.values()
            if curve_name in node_curves
        ]

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------
    @property
    def z_acceleration(self) -> Optional[Curve]:
        """Shortcut to the vertical acceleration curve."""
        return self.get_curve("z_acceleration")

    @property
    def z_velocity(self) -> Optional[Curve]:
        """Shortcut to the vertical velocity curve."""
        return self.get_curve("z_velocity")

    @property
    def resultant_velocity(self) -> Optional[Curve]:
        """Shortcut to the resultant velocity magnitude curve."""
        return self.get_curve("resultant_velocity")

    @property
    def label(self) -> str:
        """Human-readable label for plot legends and reports."""
        if self.sim_metadata:
            return self.sim_metadata.label
        return self.dir_path.name
