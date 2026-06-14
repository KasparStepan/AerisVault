"""AeroDataset — orchestrates Polars from raw α-case loads."""
from __future__ import annotations

import numpy as np

from aerocfd.analysis.coefficients import (
    dynamic_pressure, cl, cd, cm, lift_to_drag,
)
from aerocfd.analysis.rotation import body_to_wind, fluent_my_to_aero
from aerocfd.models.aircraft import Aircraft
from aerocfd.models.alpha_case import AlphaCase
from aerocfd.models.operating_condition import OperatingCondition
from aerocfd.models.polar import Polar


class AeroDataset:
    """Aerodynamic dataset for one operating condition.

    Holds raw body-frame loads + references; derives Polars on demand.
    Cases are sorted by α at construction.
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
    def fx_body_n(self) -> np.ndarray:
        return np.array([c.fx_n for c in self._cases], dtype=float)

    @property
    def fz_body_n(self) -> np.ndarray:
        return np.array([c.fz_n for c in self._cases], dtype=float)

    @property
    def my_fluent_nm(self) -> np.ndarray:
        return np.array([c.my_nm for c in self._cases], dtype=float)

    @property
    def dynamic_pressure_pa(self) -> float:
        return dynamic_pressure(
            self.operating_condition.density_kgpm3,
            self.operating_condition.velocity_mps,
        )

    def drag(self) -> Polar:
        drag_n, _ = body_to_wind(self.fx_body_n, self.fz_body_n, self.alpha_deg)
        return Polar(self.alpha_deg, drag_n, name="Drag", units="N")

    def lift(self) -> Polar:
        _, lift_n = body_to_wind(self.fx_body_n, self.fz_body_n, self.alpha_deg)
        return Polar(self.alpha_deg, lift_n, name="Lift", units="N")

    def cl(self) -> Polar:
        values = cl(self.lift().values, self.dynamic_pressure_pa,
                    self.aircraft.s_ref_m2)
        return Polar(self.alpha_deg, values, name="CL", units="-")

    def cd(self) -> Polar:
        values = cd(self.drag().values, self.dynamic_pressure_pa,
                    self.aircraft.s_ref_m2)
        return Polar(self.alpha_deg, values, name="CD", units="-")

    def lift_to_drag(self) -> Polar:
        values = lift_to_drag(self.lift().values, self.drag().values)
        return Polar(self.alpha_deg, values, name="L/D", units="-")

    def cm(self) -> Polar:
        my_aero = fluent_my_to_aero(self.my_fluent_nm)
        values = cm(my_aero, self.dynamic_pressure_pa,
                    self.aircraft.s_ref_m2, self.aircraft.c_ref_m)
        return Polar(self.alpha_deg, values, name="Cm", units="-")
