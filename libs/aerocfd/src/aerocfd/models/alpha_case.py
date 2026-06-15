"""Per-α data for one operating condition.

An AlphaCase carries either a set of per-part loads (the normal case — totals are
summed from them) or, for simple/legacy use, the body-frame totals directly. The
total_* properties present a single interface over both.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from aerocfd.models.part_load import PartLoad


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

    Provide per-part loads via `part_loads` (totals are summed from them), or the
    body-frame totals directly via fx_n/fz_n/my_nm when there are no parts. All
    values are raw Fluent body-frame quantities; the library does the body→wind
    rotation and the My sign flip.
    """
    alpha_deg: float
    fx_n: float = 0.0
    fz_n: float = 0.0
    my_nm: float = 0.0
    part_loads: tuple[PartLoad, ...] = ()
    convergence_status: ConvergenceStatus = ConvergenceStatus.UNKNOWN
    notes: str = ""

    def __post_init__(self):
        # Accept any iterable of PartLoad and freeze it as a tuple.
        object.__setattr__(self, "part_loads", tuple(self.part_loads))

    @property
    def total_fx_n(self) -> float:
        return float(sum(p.fx_n for p in self.part_loads)) if self.part_loads else self.fx_n

    @property
    def total_fz_n(self) -> float:
        return float(sum(p.fz_n for p in self.part_loads)) if self.part_loads else self.fz_n

    @property
    def total_my_nm(self) -> float:
        return float(sum(p.my_nm for p in self.part_loads)) if self.part_loads else self.my_nm
