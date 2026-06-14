"""PartLoad — one aircraft part's raw body-frame load at one α."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PartLoad:
    """Raw Fluent body-frame total for a single part at a single α.

    `group` is the analysis group the part belongs to (e.g. "Wing", "Fuselage",
    "Tail"); it is carried on the load so the library can sum per group without
    a separate part registry. Forces are SI Newtons, moment N·m, exactly as
    Fluent reports them (Fx forward-positive; My raw, sign flip in the library).
    """
    part_name: str
    group: str
    fx_n: float
    fz_n: float
    my_nm: float
