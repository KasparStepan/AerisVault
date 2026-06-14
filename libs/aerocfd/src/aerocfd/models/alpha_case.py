"""Per-α data for one operating condition (slice 1: totals only)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConvergenceStatus(str, Enum):
    CONVERGED = "converged"
    PARTIALLY_CONVERGED = "partially_converged"
    OSCILLATING = "oscillating"
    DIVERGED = "diverged"
    STOPPED_MANUALLY = "stopped_manually"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AlphaCase:
    """One Fluent run at a fixed α.

    Forces and moments are TOTALS in the body frame, exactly as Fluent reports
    them. The library does the body→wind rotation and the My sign flip; storage
    keeps the raw values.
    """
    alpha_deg: float
    fx_n: float
    fz_n: float
    my_nm: float
    convergence_status: ConvergenceStatus = ConvergenceStatus.UNKNOWN
    notes: str = ""
