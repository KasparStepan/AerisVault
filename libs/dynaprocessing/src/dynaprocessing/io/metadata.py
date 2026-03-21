"""Metadata extraction from LS-DYNA simulation directory names.

Directory naming conventions encode simulation parameters so that
the library can automatically tag results without a database lookup.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


@dataclass
class FiniteMassMetadata:
    """Metadata for a Finite Mass (drop-test) simulation.

    Attributes:
        parachute_type: E.g. 'cross', 'scrab'.
        size: Characteristic dimension, e.g. '2m'.
        mass: Payload mass, e.g. '6kg'.
        initial_velocity: E.g. '6ms'.
    """
    parachute_type: str
    size: str
    mass: str
    initial_velocity: str

    @property
    def label(self) -> str:
        return (
            f"{self.parachute_type} {self.size} | "
            f"{self.mass} ({self.initial_velocity})"
        )


@dataclass
class InfiniteMassMetadata:
    """Metadata for an Infinite Mass (wind-tunnel / ICFD) simulation.

    Attributes:
        parachute_type: E.g. 'scrab'.
        size: Characteristic dimension, e.g. '2m'.
        flow_velocity: Free-stream velocity, e.g. '40ms'.
        simulation_type: E.g. 'folded', 'inflated'.
        additional_info: Any remaining tokens from the directory name.
    """
    parachute_type: str
    size: str
    flow_velocity: str
    simulation_type: str
    additional_info: str = ""

    @property
    def label(self) -> str:
        return (
            f"{self.parachute_type} {self.size} | "
            f"{self.flow_velocity} ({self.simulation_type})"
        )


def parse_finite_mass_directory(directory_path: str | Path) -> FiniteMassMetadata:
    """Parse a Finite Mass directory name into structured metadata.

    Expected format: ``{parachute_type}_{size}_{mass}_{initial_velocity}``
    Example: ``cross_2m_6kg_6ms``

    Args:
        directory_path: Path to the simulation directory.

    Returns:
        Populated FiniteMassMetadata dataclass.

    Raises:
        ValueError: If the directory name doesn't match the expected format.
    """
    dirname = Path(directory_path).name
    parts = dirname.split("_")

    if len(parts) != 4:
        raise ValueError(
            f"Invalid finite mass directory name: '{dirname}'. "
            f"Expected 4 underscore-separated parts "
            f"(type_size_mass_velocity), found {len(parts)}."
        )

    return FiniteMassMetadata(
        parachute_type=parts[0],
        size=parts[1],
        mass=parts[2],
        initial_velocity=parts[3],
    )


def parse_infinite_mass_directory(
    directory_path: str | Path,
) -> InfiniteMassMetadata:
    """Parse an Infinite Mass directory name into structured metadata.

    Expected format: ``{parachute_type}_{size}_{flow_velocity}_{sim_type}[_{extra}]``
    Example: ``scrab_2m_40ms_folded``

    Args:
        directory_path: Path to the simulation directory.

    Returns:
        Populated InfiniteMassMetadata dataclass.

    Raises:
        ValueError: If the directory name doesn't match the expected format.
    """
    dirname = Path(directory_path).name
    parts = dirname.split("_")

    if len(parts) < 4:
        raise ValueError(
            f"Invalid infinite mass directory name: '{dirname}'. "
            f"Expected at least 4 underscore-separated parts "
            f"(type_size_velocity_simtype), found {len(parts)}."
        )

    return InfiniteMassMetadata(
        parachute_type=parts[0],
        size=parts[1],
        flow_velocity=parts[2],
        simulation_type=parts[3],
        additional_info="_".join(parts[4:]) if len(parts) > 4 else "",
    )
