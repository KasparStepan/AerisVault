"""Aerodynamic coefficient definitions (SI throughout)."""
from __future__ import annotations

import numpy as np


def dynamic_pressure(density_kgpm3, velocity_mps):
    """q∞ = ½ρV²."""
    return 0.5 * density_kgpm3 * velocity_mps**2


def cl(lift_n, q_pa, s_ref_m2):
    return lift_n / (q_pa * s_ref_m2)


def cd(drag_n, q_pa, s_ref_m2):
    return drag_n / (q_pa * s_ref_m2)


def cm(my_aero_nm, q_pa, s_ref_m2, c_ref_m):
    """Pitching-moment coefficient. Caller must pass My already in aerospace
    convention (i.e. after fluent_my_to_aero)."""
    return my_aero_nm / (q_pa * s_ref_m2 * c_ref_m)


def lift_to_drag(lift_n, drag_n):
    """L/D, element-wise. Drag = 0 → +∞ (or −∞ if lift is negative)."""
    drag_arr = np.asarray(drag_n, dtype=float)
    lift_arr = np.asarray(lift_n, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(drag_arr == 0.0, np.sign(lift_arr) * np.inf, lift_arr / drag_arr)
    if result.ndim == 0:
        return float(result)
    return result
