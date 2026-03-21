"""Post-processing pipeline for LS-DYNA simulation results.

The ``Job`` class provides a declarative interface: you describe *what*
you want (which variables, which filters, which outputs) and call
``process()`` to execute the entire pipeline.

The pipeline cleanly separates:
- **Data loading** — detecting simulation type and parsing files.
- **Processing** — filtering, unit conversion, derived quantities.
- **Visualization** — delegated to the ``viz`` package (optional).
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dynaprocessing.models.curve import Curve
from dynaprocessing.models.finite_mass import FiniteMassSimulation
from dynaprocessing.models.infinite_mass import InfiniteMassSimulation

logger = logging.getLogger(__name__)


class Job:
    """Declarative post-processing job for LS-DYNA results.

    Example::

        job = Job(
            directory="results/cross_2m_6kg_6ms",
            variables=["z_acceleration", "resultant_velocity"],
            to_G=True,
            filter_type="cfc",
            filter_settings=60,
        )
        curves = job.process()  # returns list of processed Curves

    Args:
        directory: Path to the simulation results directory.
        variables: List of curve names to extract and process.
        to_G: If True, convert acceleration curves from m/s² to G.
        filter_type: Filter to apply: 'cfc', 'butterworth', or
            'moving_average'. None to skip filtering.
        filter_settings: Filter parameter(s). For CFC: the class number.
            For Butterworth: cutoff_freq or (cutoff_freq, order).
            For moving average: window size.
        calc_drag_coeff: If True, compute Cd for force-like curves.
        velocity: Reference velocity for Cd calculation (m/s).
        area: Reference area for Cd calculation (m²).
        rho: Air density for Cd calculation (kg/m³, default 1.225).
    """

    def __init__(
        self,
        directory: Union[str, Path],
        variables: List[str],
        to_G: bool = False,
        filter_type: Optional[str] = None,
        filter_settings: Any = None,
        calc_drag_coeff: bool = False,
        velocity: Optional[float] = None,
        area: Optional[float] = None,
        rho: float = 1.225,
    ) -> None:
        self.directory = Path(directory)
        self.variables = variables

        # Processing flags
        self.to_G = to_G
        self.filter_type = filter_type
        self.filter_settings = filter_settings

        # Aerodynamics flags
        self.calc_drag_coeff = calc_drag_coeff
        self.velocity = velocity
        self.area = area
        self.rho = rho

        # Internal state
        self.simulation: Optional[
            FiniteMassSimulation | InfiniteMassSimulation
        ] = None
        self.processed_curves: List[Curve] = []

    # ------------------------------------------------------------------
    # Pipeline stages
    # ------------------------------------------------------------------

    def _load_simulation(self) -> None:
        """Detect simulation type from directory contents and load it."""
        if not self.directory.exists():
            raise FileNotFoundError(
                f"Simulation directory not found: {self.directory}"
            )

        has_csv = (
            list(self.directory.glob("All_data.csv"))
            or list(self.directory.glob("Accel.csv"))
        )
        has_dat = list(self.directory.glob("*.dat"))

        if has_csv:
            self.simulation = FiniteMassSimulation(self.directory)
            logger.info("Detected Finite Mass simulation.")
        elif has_dat:
            self.simulation = InfiniteMassSimulation(self.directory)
            logger.info("Detected Infinite Mass simulation.")
        else:
            raise ValueError(
                f"Cannot determine simulation type in {self.directory}. "
                f"Expected .csv or .dat files."
            )

    def _apply_filter(self, curve: Curve) -> Curve:
        """Apply the configured filter to a single curve.

        Returns a new (filtered) Curve; the original is untouched.
        """
        if not self.filter_type:
            return curve

        ft = self.filter_type.strip().lower()

        if ft == "cfc":
            cfc_val = float(self.filter_settings) if self.filter_settings is not None else 60.0
            return curve.apply_cfc_filter(cfc=cfc_val)

        if ft == "butterworth":
            if isinstance(self.filter_settings, (tuple, list)):
                return curve.apply_butterworth_filter(
                    cutoff_freq=float(self.filter_settings[0]),
                    order=int(self.filter_settings[1]),
                )
            return curve.apply_butterworth_filter(
                cutoff_freq=float(self.filter_settings)
            )

        if ft in ("moving_average", "mov_average", "moving average"):
            ws = int(self.filter_settings) if self.filter_settings is not None else 5
            return curve.apply_moving_average_filter(window_size=ws)

        logger.warning("Unknown filter type '%s'. Skipping.", ft)
        return curve

    def _extract_and_process(self) -> List[Curve]:
        """Extract requested variables, apply filters and conversions.

        Returns:
            List of processed Curve objects.
        """
        assert self.simulation is not None

        results: List[Curve] = []

        for var_name in self.variables:
            curve = self.simulation.get_curve(var_name)
            if curve is None:
                logger.warning(
                    "Variable '%s' not found in %s. Skipping.",
                    var_name, self.directory.name,
                )
                continue

            # 1. Filter
            curve = self._apply_filter(curve)

            # 2. Unit conversion
            if self.to_G and "acceleration" in curve.name.lower():
                curve = curve.to_g()

            results.append(curve)

            # 3. Drag coefficient (if requested and curve is force-like)
            if self.calc_drag_coeff and (
                "fpx" in curve.name.lower()
                or "fpy" in curve.name.lower()
                or "fpz" in curve.name.lower()
                or "force" in curve.name.lower()
            ):
                if self.velocity is None or self.area is None:
                    raise ValueError(
                        "Velocity and Area must be provided to "
                        "calculate drag coefficient."
                    )
                cd_curve = curve.calculate_drag_coefficient(
                    v=self.velocity, A=self.area, rho=self.rho
                )
                results.append(cd_curve)

        return results

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self) -> List[Curve]:
        """Execute the full processing pipeline.

        Loads the simulation, extracts the requested variables, applies
        filters and conversions, and returns the processed Curve list.

        This method does **not** create any plots or write any files.
        Use the ``viz`` module or ``Curve.to_parquet()`` for output.

        Returns:
            List of processed Curve objects.
        """
        self._load_simulation()
        self.processed_curves = self._extract_and_process()

        if not self.processed_curves:
            logger.warning("No valid curves processed from %s.", self.directory)

        return self.processed_curves
