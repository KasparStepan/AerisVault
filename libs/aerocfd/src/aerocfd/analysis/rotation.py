"""Body↔wind rotation and Cm sign convention.

Axis convention (the contract):
- Body frame: x = forward, z = up, right-handed → y points to the left.
- α positive = nose up.
- Fluent reports loads in this fixed body frame regardless of α.
- Sideslip is ignored in v1 (β = 0); rotation stays in the x–z plane.
"""
from __future__ import annotations

import numpy as np


def body_to_wind(fx_n, fz_n, alpha_deg):
    """Rotate body-frame total force (force ON the body, x forward, z up)
    to wind frame. Returns (drag_n, lift_n). Scalars or numpy arrays.

    Fluent's Fx is forward-positive, so the drag-producing axial force is
    negative — hence the minus sign on the Fx drag term:

        drag = -Fx·cos(α) + Fz·sin(α)
        lift =  Fx·sin(α) + Fz·cos(α)

    At α=0: drag = -Fx (positive for a draggy body), lift = Fz.
    """
    alpha_rad = np.radians(alpha_deg)
    cos_a = np.cos(alpha_rad)
    sin_a = np.sin(alpha_rad)
    drag_n = -fx_n * cos_a + fz_n * sin_a
    lift_n =  fx_n * sin_a + fz_n * cos_a
    return drag_n, lift_n


def fluent_my_to_aero(my_fluent_nm):
    """Flip the sign of Fluent's My to match aerospace Cm convention.

    With body y pointing left, Fluent's right-hand-rule My is nose-DOWN positive.
    Aerospace Cm convention is nose-UP positive. So:
        My_aero = -My_fluent
    """
    return -my_fluent_nm
