"""PartLoad — one aircraft part's raw body-frame load at one α."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PartLoad:
    """Raw Fluent body-frame total for a single part at a single α.

    `group` is the analysis group the part belongs to (e.g. "Wing", "Fuselage",
    "Tail"); it is carried on the load so the library can sum per group without
    a separate part registry. Forces are SI Newtons, moment N·m, exactly as
    Fluent reports them (Fx forward-positive; My raw, sign flip in the library).

    The pitching moment can be given at several reference points via `moments`
    (a tuple of (reference_label, my_nm) pairs) — e.g. one entry per CG position
    (20%/25%/30% MAC). `my_nm` is the single-reference fallback used when no
    reference is requested.
    """
    part_name: str
    group: str
    fx_n: float
    fz_n: float
    my_nm: float = 0.0
    moments: tuple[tuple[str, float], ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "moments", tuple(self.moments))

    def moment_for(self, reference: Optional[str]) -> float:
        """Pitching moment at a reference point. reference=None → the single
        `my_nm`; a label → its value from `moments` (0.0 if not present)."""
        if reference is None:
            return self.my_nm
        return dict(self.moments).get(reference, 0.0)
