"""Compare two polars of the same coefficient on a common α grid."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from aerocfd.models.polar import Polar


@dataclass(frozen=True)
class ComparisonResult:
    """Two polars sampled on a shared α grid, plus their difference.

    `delta` is B − A. `name` is the coefficient compared (taken from polar A,
    e.g. "CL"). The A/B identities (which dataset) are supplied by the caller.
    """
    name: str
    alpha_deg: np.ndarray
    values_a: np.ndarray
    values_b: np.ndarray
    delta: np.ndarray


def compare_polars(
    polar_a: Polar, polar_b: Polar, alpha_grid: Optional[np.ndarray] = None
) -> ComparisonResult:
    """Sample both polars on a common α grid and return their values + difference.

    With no grid, the grid is the α values present in BOTH polars (their
    intersection), sorted. A custom grid interpolates each polar (numpy.interp
    clips at the polar's range).
    """
    if alpha_grid is None:
        common = set(polar_a.alpha_deg.tolist()) & set(polar_b.alpha_deg.tolist())
        alpha_grid = np.array(sorted(common), dtype=float)
    else:
        alpha_grid = np.asarray(alpha_grid, dtype=float)

    values_a = np.array([polar_a.interpolate_at(alpha) for alpha in alpha_grid])
    values_b = np.array([polar_b.interpolate_at(alpha) for alpha in alpha_grid])
    return ComparisonResult(
        name=polar_a.name,
        alpha_deg=alpha_grid,
        values_a=values_a,
        values_b=values_b,
        delta=values_b - values_a,
    )
