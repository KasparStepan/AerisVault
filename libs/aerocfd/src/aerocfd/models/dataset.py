"""AeroDataset — orchestrates Polars from raw α-case loads.

Each polar method takes an optional `group`:
- group=None → totals (every part, or the case totals when there are no parts).
- group="Wing" → only that group's contribution.
Group contributions sum to the total (coefficients add at a fixed S_ref).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from aerocfd.analysis.coefficients import (
    dynamic_pressure, cl, cd, cm, lift_to_drag,
)
from aerocfd.analysis.rotation import body_to_wind, fluent_my_to_aero
from aerocfd.analysis.summation import group_names, my_sum, wind_force_sum
from aerocfd.models.aircraft import Aircraft
from aerocfd.models.alpha_case import AlphaCase
from aerocfd.models.operating_condition import OperatingCondition
from aerocfd.models.polar import Polar


def _suffix(group: Optional[str]) -> str:
    return f" ({group})" if group else ""


class AeroDataset:
    """Aerodynamic dataset for one operating condition.

    Holds raw body-frame loads + references; derives Polars on demand. Cases are
    sorted by α at construction.
    """

    def __init__(
        self,
        aircraft: Aircraft,
        operating_condition: OperatingCondition,
        alpha_cases: list[AlphaCase],
    ):
        self.aircraft = aircraft
        self.operating_condition = operating_condition
        self._cases = sorted(alpha_cases, key=lambda c: c.alpha_deg)

    @property
    def alpha_deg(self) -> np.ndarray:
        return np.array([c.alpha_deg for c in self._cases], dtype=float)

    @property
    def dynamic_pressure_pa(self) -> float:
        return dynamic_pressure(
            self.operating_condition.density_kgpm3,
            self.operating_condition.velocity_mps,
        )

    def groups(self) -> list[str]:
        """Distinct analysis groups present (e.g. ['Wing', 'Fuselage', 'Tail'])."""
        return group_names(self._cases)

    # --- wind-frame forces and moment, total or per group ---

    def _wind_force_arrays(self, group: Optional[str]) -> tuple[np.ndarray, np.ndarray]:
        drags, lifts = [], []
        for case in self._cases:
            if group is None and not case.part_loads:
                # Totals path (no parts): rotate the case's body-frame totals.
                drag, lift = body_to_wind(case.total_fx_n, case.total_fz_n, case.alpha_deg)
            else:
                drag, lift = wind_force_sum(case.part_loads, case.alpha_deg, group)
            drags.append(drag)
            lifts.append(lift)
        return np.array(drags), np.array(lifts)

    def _my_array(self, group: Optional[str]) -> np.ndarray:
        if group is None:
            return np.array([c.total_my_nm for c in self._cases], dtype=float)
        return np.array([my_sum(c.part_loads, group) for c in self._cases], dtype=float)

    # --- polars ---

    def drag(self, group: Optional[str] = None) -> Polar:
        drag_n, _ = self._wind_force_arrays(group)
        return Polar(self.alpha_deg, drag_n, name="Drag" + _suffix(group), units="N")

    def lift(self, group: Optional[str] = None) -> Polar:
        _, lift_n = self._wind_force_arrays(group)
        return Polar(self.alpha_deg, lift_n, name="Lift" + _suffix(group), units="N")

    def cl(self, group: Optional[str] = None) -> Polar:
        values = cl(self.lift(group).values, self.dynamic_pressure_pa, self.aircraft.s_ref_m2)
        return Polar(self.alpha_deg, values, name="CL" + _suffix(group), units="-")

    def cd(self, group: Optional[str] = None) -> Polar:
        values = cd(self.drag(group).values, self.dynamic_pressure_pa, self.aircraft.s_ref_m2)
        return Polar(self.alpha_deg, values, name="CD" + _suffix(group), units="-")

    def lift_to_drag(self, group: Optional[str] = None) -> Polar:
        values = lift_to_drag(self.lift(group).values, self.drag(group).values)
        return Polar(self.alpha_deg, values, name="L/D" + _suffix(group), units="-")

    def cm(self, group: Optional[str] = None) -> Polar:
        my_aero = fluent_my_to_aero(self._my_array(group))
        values = cm(my_aero, self.dynamic_pressure_pa, self.aircraft.s_ref_m2, self.aircraft.c_ref_m)
        return Polar(self.alpha_deg, values, name="Cm" + _suffix(group), units="-")
