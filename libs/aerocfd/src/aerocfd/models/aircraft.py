"""Aircraft reference values and identity."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Aircraft:
    """Reference values for one aircraft.

    All references are SI: areas in m², lengths in m. The axis convention
    string is the contract that downstream rotation/sign-flip code relies on.
    """
    name: str
    s_ref_m2: float
    c_ref_m: float
    b_ref_m: float
    axis_convention: str = "x_fwd_z_up_rh"
    description: str = ""
