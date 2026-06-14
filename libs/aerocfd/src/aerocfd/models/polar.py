"""Polar — a 1D ordered series indexed by angle of attack."""
from __future__ import annotations

import numpy as np


class Polar:
    """1D ordered series indexed by angle of attack.

    Polar is the aerocfd analogue of dynaprocessing's Curve, with α as the
    independent variable instead of time. Immutable by convention: methods
    that transform a Polar return a new instance.
    """

    def __init__(
        self,
        alpha_deg: np.ndarray,
        values: np.ndarray,
        name: str = "Unknown",
        units: str | None = None,
        metadata: dict | None = None,
    ):
        alpha_deg = np.asarray(alpha_deg, dtype=float)
        values = np.asarray(values, dtype=float)
        if alpha_deg.shape != values.shape:
            raise ValueError(
                f"alpha_deg shape {alpha_deg.shape} != values shape {values.shape}"
            )
        # Sort by alpha so interpolate_at and slice_alpha can rely on monotonic input.
        order = np.argsort(alpha_deg)
        self._alpha_deg = alpha_deg[order]
        self._values = values[order]
        self.name = name
        self.units = units
        self.metadata = dict(metadata) if metadata else {}

    @property
    def alpha_deg(self) -> np.ndarray:
        return self._alpha_deg

    @property
    def values(self) -> np.ndarray:
        return self._values

    def interpolate_at(self, alpha_deg: float) -> float:
        """Linear interpolation. Clips at the polar's α range (numpy.interp default)."""
        return float(np.interp(alpha_deg, self._alpha_deg, self._values))

    def slice_alpha(self, alpha_min: float, alpha_max: float) -> "Polar":
        """Return a new Polar containing only points with α ∈ [alpha_min, alpha_max]."""
        mask = (self._alpha_deg >= alpha_min) & (self._alpha_deg <= alpha_max)
        return Polar(
            alpha_deg=self._alpha_deg[mask],
            values=self._values[mask],
            name=self.name,
            units=self.units,
            metadata=self.metadata,
        )
