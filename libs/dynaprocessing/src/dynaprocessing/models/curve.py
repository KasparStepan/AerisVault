"""Core Curve class — the fundamental time-series data container.

A Curve represents a single physical quantity (acceleration, force, velocity, etc.)
recorded over time from an LS-DYNA simulation. All filter and conversion operations
return **new** Curve instances, keeping the original data immutable.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
STANDARD_GRAVITY = 9.80665  # m/s^2


class Curve:
    """Immutable time-series data container for LS-DYNA post-processing.

    All filter/transform operations return a **new** Curve, preserving the
    original data. This makes it safe to compare raw vs. filtered signals
    and avoids accidental double-conversions (e.g., calling ``to_g()`` twice).

    Args:
        time: 1-D array of time stamps in seconds.
        values: 1-D array of measured values, same length as *time*.
        name: Human-readable property name (e.g., 'z_acceleration').
        node_id: LS-DYNA node ID the data was extracted from.
        units: Physical units string (e.g., 'm/s^2', 'N', 'G').
        metadata: Arbitrary extra metadata dictionary.
        filter_history: Ordered list of operations already applied.

    Raises:
        TypeError: If *time* or *values* are not array-like.
        ValueError: If arrays are empty or have mismatched lengths.
    """

    def __init__(
        self,
        time: np.ndarray,
        values: np.ndarray,
        name: str = "Unknown",
        node_id: Optional[str] = None,
        units: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        filter_history: Optional[List[str]] = None,
    ) -> None:
        # ---- Input validation ------------------------------------------------
        try:
            time = np.asarray(time, dtype=float)
            values = np.asarray(values, dtype=float)
        except (ValueError, TypeError) as exc:
            raise TypeError(
                f"'time' and 'values' must be numeric array-like, got "
                f"time={type(time).__name__}, values={type(values).__name__}"
            ) from exc

        if time.ndim != 1 or values.ndim != 1:
            raise ValueError(
                f"'time' and 'values' must be 1-D arrays, got "
                f"time.ndim={time.ndim}, values.ndim={values.ndim}"
            )
        if len(time) == 0:
            raise ValueError("'time' and 'values' must not be empty.")
        if len(time) != len(values):
            raise ValueError(
                f"Length mismatch: time has {len(time)} points, "
                f"values has {len(values)} points."
            )

        # ---- Store immutable copies -----------------------------------------
        self._time: np.ndarray = time.copy()
        self._values: np.ndarray = values.copy()

        # Make arrays read-only to enforce immutability
        self._time.flags.writeable = False
        self._values.flags.writeable = False

        self.name: str = name
        self.node_id: Optional[str] = node_id
        self.units: Optional[str] = units
        self.metadata: Dict[str, Any] = metadata or {}
        self.filter_history: List[str] = list(filter_history or [])

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------
    @property
    def time(self) -> np.ndarray:
        """Time stamps array (read-only)."""
        return self._time

    @property
    def values(self) -> np.ndarray:
        """Data values array (read-only)."""
        return self._values

    # ------------------------------------------------------------------
    # Private helper: create a derived Curve
    # ------------------------------------------------------------------
    def _derive(
        self,
        new_values: np.ndarray,
        operation: str,
        *,
        new_name: Optional[str] = None,
        new_units: Optional[str] = None,
        new_time: Optional[np.ndarray] = None,
    ) -> Curve:
        """Create a new Curve from this one with modified values/metadata."""
        history = self.filter_history + [operation]
        return Curve(
            time=new_time if new_time is not None else self._time.copy(),
            values=new_values,
            name=new_name or self.name,
            node_id=self.node_id,
            units=new_units or self.units,
            metadata=deepcopy(self.metadata),
            filter_history=history,
        )

    # ------------------------------------------------------------------
    # Filtering operations (all return NEW Curves)
    # ------------------------------------------------------------------
    def apply_cfc_filter(self, cfc: int = 60) -> Curve:
        """Apply an SAE CFC (Channel Frequency Class) filter.

        Args:
            cfc: CFC class (e.g. 60, 180, 600, 1000).

        Returns:
            New Curve with filtered values.
        """
        from dynaprocessing.analysis.filters import apply_cfc_filter
        filtered = apply_cfc_filter(self._time, self._values, cfc=cfc)
        return self._derive(filtered, f"CFC-{cfc}")

    def apply_butterworth_filter(
        self, cutoff_freq: float = 60.0, order: int = 2
    ) -> Curve:
        """Apply a phased-compensated Butterworth low-pass filter.

        Args:
            cutoff_freq: Cutoff frequency in Hz.
            order: Filter order.

        Returns:
            New Curve with filtered values.
        """
        from dynaprocessing.analysis.filters import apply_butterworth_filter
        filtered = apply_butterworth_filter(
            self._time, self._values, cutoff_freq, order
        )
        return self._derive(
            filtered, f"Butterworth(fc={cutoff_freq}, order={order})"
        )

    def apply_moving_average_filter(self, window_size: int = 5) -> Curve:
        """Apply a moving average smoothing filter.

        Args:
            window_size: Number of points in the averaging window.

        Returns:
            New Curve with smoothed values.
        """
        from dynaprocessing.analysis.filters import apply_moving_average_filter
        filtered = apply_moving_average_filter(self._values, window_size)
        return self._derive(filtered, f"MovingAvg(w={window_size})")

    def apply_savgol_filter(
        self, window_length: int = 51, polyorder: int = 3
    ) -> Curve:
        """Apply a Savitzky-Golay smoothing filter.

        Args:
            window_length: Number of points in the filter window.
            polyorder: Polynomial order for the local fit.

        Returns:
            New Curve with smoothed values.
        """
        from dynaprocessing.analysis.filters import apply_savgol_filter
        filtered = apply_savgol_filter(
            self._values, window_length, polyorder
        )
        return self._derive(
            filtered, f"SavGol(w={window_length}, p={polyorder})"
        )

    # ------------------------------------------------------------------
    # Unit conversions (return NEW Curves)
    # ------------------------------------------------------------------
    def to_g(self) -> Curve:
        """Convert acceleration from m/s² to G-units.

        Returns:
            New Curve with values in G and units='G'.
        """
        return self._derive(
            self._values / STANDARD_GRAVITY,
            "to_G",
            new_units="G",
        )

    # ------------------------------------------------------------------
    # Derived quantities
    # ------------------------------------------------------------------
    def calculate_drag_coefficient(
        self, v: float, A: float, rho: float = 1.225
    ) -> Curve:
        """Calculate dimensionless drag coefficient Cd = 2F / (ρ·v²·A).

        Args:
            v: Reference flow velocity in m/s.
            A: Reference area in m².
            rho: Air density in kg/m³ (default ISA sea-level 1.225).

        Returns:
            New Curve representing the drag coefficient time history.

        Raises:
            ValueError: If v or A are zero.
        """
        if v == 0 or A == 0:
            raise ValueError(
                "Velocity (v) and Area (A) must be > 0 to calculate Cd."
            )

        cd_values = (2.0 * self._values) / (rho * (v ** 2) * A)

        return self._derive(
            cd_values,
            f"Cd(v={v}, A={A}, rho={rho})",
            new_name=f"{self.name}_Cd",
            new_units="dimensionless",
        )

    def to_force(self, mass: float) -> Curve:
        """Convert an acceleration curve to force: F = m × a.

        Typical use: finite mass drop test where acceleration is measured
        directly and you need the aerodynamic drag force.

        Args:
            mass: Payload mass in kg.

        Returns:
            New Curve with force values in Newtons.

        Raises:
            ValueError: If mass is zero or negative.
        """
        if mass <= 0:
            raise ValueError(f"Mass must be positive, got {mass} kg.")

        force_values = mass * self._values
        return self._derive(
            force_values,
            f"F=m*a(m={mass})",
            new_name=f"{self.name}_force",
            new_units="N",
        )

    def calculate_cds(self, v: float, rho: float = 1.225) -> Curve:
        """Calculate drag area CdS = 2·F / (ρ·v²) with constant velocity.

        This is the product of drag coefficient and reference area (Cd × S).
        Useful when the reference area is not known or not well-defined.

        Typically used for infinite mass (wind-tunnel) results where the
        flow velocity is constant throughout the simulation.

        Args:
            v: Constant flow velocity in m/s.
            rho: Air density in kg/m³ (default ISA sea-level).

        Returns:
            New Curve representing CdS time history in m².

        Raises:
            ValueError: If v is zero.
        """
        if v == 0:
            raise ValueError("Velocity must be non-zero to compute CdS.")

        dynamic_pressure = 0.5 * rho * v ** 2
        cds_values = self._values / dynamic_pressure
        return self._derive(
            cds_values,
            f"CdS(v={v}, rho={rho})",
            new_name=f"{self.name}_CdS",
            new_units="m^2",
        )

    def calculate_cds_from_velocity(
        self, velocity_curve: Curve, rho: float = 1.225
    ) -> Curve:
        """Calculate drag area CdS = 2·F / (ρ·v²(t)) with time-varying velocity.

        Used for finite mass (drop test) simulations where the payload
        decelerates over time and velocity is measured as a separate channel.

        Points where |v(t)| < 0.1 m/s are set to NaN (CdS is physically
        undefined when the payload is nearly stationary).

        Args:
            velocity_curve: Velocity time history (must share the same time base).
            rho: Air density in kg/m³.

        Returns:
            New Curve representing CdS time history in m².

        Raises:
            ValueError: If the curves have different lengths.
        """
        if len(self._values) != len(velocity_curve.values):
            raise ValueError(
                f"Force curve has {len(self._values)} points but velocity curve "
                f"has {len(velocity_curve.values)} points. They must match."
            )

        velocity_values = velocity_curve.values
        near_zero = np.abs(velocity_values) <= 0.1
        dynamic_pressure = 0.5 * rho * velocity_values ** 2

        # CdS is physically undefined when the payload is nearly stationary.
        # Suppress the divide-by-zero from the masked-out elements; np.where
        # discards them anyway, but it still evaluates the division eagerly.
        with np.errstate(divide="ignore", invalid="ignore"):
            cds_values = np.where(
                near_zero,
                np.nan,
                self._values / dynamic_pressure,
            )

        return self._derive(
            cds_values,
            f"CdS_variable_v(rho={rho})",
            new_name=f"{self.name}_CdS",
            new_units="m^2",
        )

    # ------------------------------------------------------------------
    # Multi-component operations
    # ------------------------------------------------------------------
    @staticmethod
    def resultant(*components: Curve) -> Curve:
        """Calculate resultant magnitude from component curves.

        Computes |F| = sqrt(F1² + F2² + ... + Fn²) point-by-point.
        Typical use: resultant force from Fpx, Fpy, Fpz components.

        All input curves must share the same time array (same length
        and values).

        Args:
            *components: Two or more component Curve objects.

        Returns:
            New Curve with the resultant magnitude.

        Raises:
            ValueError: If fewer than 2 components or mismatched lengths.
        """
        if len(components) < 2:
            raise ValueError(
                f"Need at least 2 component curves, got {len(components)}."
            )

        n_points = len(components[0])
        for c in components[1:]:
            if len(c) != n_points:
                raise ValueError(
                    f"All components must have the same length. "
                    f"'{components[0].name}' has {n_points} points, "
                    f"'{c.name}' has {len(c)} points."
                )

        sum_of_squares = sum(c.values ** 2 for c in components)
        resultant_values = np.sqrt(sum_of_squares)

        # Build a descriptive name from component names
        component_names = ", ".join(c.name for c in components)
        units = components[0].units

        return Curve(
            time=components[0].time.copy(),
            values=resultant_values,
            name="resultant_force",
            units=units,
            filter_history=[f"resultant({component_names})"],
        )

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    def get_max(self) -> tuple[float, float]:
        """Return (max_value, time_at_max)."""
        idx = int(np.argmax(self._values))
        return float(self._values[idx]), float(self._time[idx])

    def get_min(self) -> tuple[float, float]:
        """Return (min_value, time_at_min)."""
        idx = int(np.argmin(self._values))
        return float(self._values[idx]), float(self._time[idx])

    def statistics(self) -> dict:
        """Calculate basic descriptive statistics.

        Returns:
            Dictionary with mean, std, min, max, rms, median.
        """
        from dynaprocessing.analysis.statistics import basic_statistics
        return basic_statistics(self)

    def derivative(self, order: int = 1, smooth: bool = False) -> Curve:
        """Calculate time derivative.

        Args:
            order: Derivative order (1 or 2).
            smooth: Apply smoothing before differentiation.

        Returns:
            New Curve representing the derivative.

        Raises:
            ValueError: If *order* is not 1 or 2.
        """
        from dynaprocessing.analysis.derivatives import (
            first_derivative,
            second_derivative,
        )
        if order == 1:
            return first_derivative(self, smooth=smooth)
        if order == 2:
            return second_derivative(self, smooth=smooth)
        raise ValueError(f"Only order 1 or 2 supported, got {order}.")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def to_dataframe(self) -> pd.DataFrame:
        """Export the curve as a two-column pandas DataFrame.

        Columns are named ``'time'`` and the curve's ``name``.
        """
        return pd.DataFrame({
            "time": self._time.copy(),
            self.name: self._values.copy(),
        })

    def to_parquet(self, filepath: str | Path) -> Path:
        """Export the curve to a Parquet file for fast web rendering.

        Args:
            filepath: Destination path (will be created/overwritten).

        Returns:
            Resolved Path to the written file.
        """
        out = Path(filepath).resolve()
        self.to_dataframe().to_parquet(out, index=False)
        logger.info("Curve '%s' exported to %s", self.name, out)
        return out

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._time)

    def __repr__(self) -> str:
        filter_str = (
            f", filters={self.filter_history}" if self.filter_history else ""
        )
        return (
            f"<Curve(name='{self.name}', node='{self.node_id}', "
            f"points={len(self)}, units='{self.units}'{filter_str})>"
        )
