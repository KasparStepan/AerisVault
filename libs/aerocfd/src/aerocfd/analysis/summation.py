"""Sum per-part loads into group and total contributions.

Rule (spec §7.5): rotate each part's load to the wind frame first, then sum.
Mathematically equal to summing in the body frame and rotating once (rotation is
linear), but engineering questions ("what does the Wing contribute to lift?")
live in the wind frame, so the code reads that way.
"""
from __future__ import annotations

from typing import Iterable, Optional

from aerocfd.analysis.rotation import body_to_wind
from aerocfd.models.part_load import PartLoad


def wind_force_sum(
    part_loads: Iterable[PartLoad], alpha_deg: float, group: Optional[str] = None
) -> tuple[float, float]:
    """Return (drag_n, lift_n) summed over the parts (or just one group) at α.

    group=None sums every part; a group name sums only parts in that group.
    """
    drag_total = 0.0
    lift_total = 0.0
    for load in part_loads:
        if group is None or load.group == group:
            drag, lift = body_to_wind(load.fx_n, load.fz_n, alpha_deg)
            drag_total += drag
            lift_total += lift
    return drag_total, lift_total


def my_sum(
    part_loads: Iterable[PartLoad], group: Optional[str] = None,
    reference: Optional[str] = None,
) -> float:
    """Sum raw Fluent My over the parts (or one group), at one reference point.
    My is invariant under the in-plane body→wind rotation, so it sums directly;
    the sign flip is applied later. reference=None uses each part's single my_nm."""
    return float(sum(
        p.moment_for(reference) for p in part_loads if group is None or p.group == group
    ))


def group_names(cases) -> list[str]:
    """Distinct group names across all cases, in first-seen order."""
    seen: list[str] = []
    for case in cases:
        for load in case.part_loads:
            if load.group not in seen:
                seen.append(load.group)
    return seen
