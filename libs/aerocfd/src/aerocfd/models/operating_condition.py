"""Operating condition (one Fluent setup, varying α)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperatingCondition:
    """Free-stream conditions for one fixed Fluent setup."""
    name: str
    velocity_mps: float
    density_kgpm3: float
    description: str = ""
