"""DynaProcessing — LS-DYNA post-processing library for AerisVault.

Public API example::

    from dynaprocessing import Curve, Job, FiniteMassSimulation
    from dynaprocessing.viz import plot_curves, plot_curves_plotly

    # Process simulation results
    job = Job(
        directory="results/cross_2m_6kg_6ms",
        variables=["z_acceleration"],
        to_G=True,
        filter_type="cfc",
        filter_settings=60,
    )
    curves = job.process()

    # Plot with Matplotlib
    plot_curves(curves, title="Z-Acceleration")

    # Or export to Parquet for web rendering
    for curve in curves:
        curve.to_parquet(f"output/{curve.name}.parquet")
"""

from dynaprocessing.models.curve import Curve
from dynaprocessing.models.simulation import BaseSimulation, SimulationMetadata
from dynaprocessing.models.finite_mass import FiniteMassSimulation
from dynaprocessing.models.infinite_mass import InfiniteMassSimulation
from dynaprocessing.analysis.postprocess import Job

# Analysis utilities — importable as dynaprocessing.analysis.*
from dynaprocessing.analysis import (
    basic_statistics,
    peak_detection,
    settling_time,
    frequency_analysis,
    auto_detect_events,
    align_curves,
    calculate_rmse,
    compare_statistics,
    first_derivative,
    second_derivative,
)

__all__ = [
    "Curve",
    "BaseSimulation",
    "SimulationMetadata",
    "FiniteMassSimulation",
    "InfiniteMassSimulation",
    "Job",
    # Analysis shortcuts
    "basic_statistics",
    "peak_detection",
    "settling_time",
    "frequency_analysis",
    "auto_detect_events",
    "align_curves",
    "calculate_rmse",
    "compare_statistics",
    "first_derivative",
    "second_derivative",
]

