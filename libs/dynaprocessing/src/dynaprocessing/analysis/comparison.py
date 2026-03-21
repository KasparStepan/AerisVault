"""Comparison utilities for multiple simulation curves.

Provides time-series alignment, RMSE calculation, difference curves,
and cross-simulation statistical comparison — all operating on
``Curve`` objects.
"""

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

from dynaprocessing.models.curve import Curve
from dynaprocessing.analysis.statistics import basic_statistics

logger = logging.getLogger(__name__)


def align_curves(curves: List[Curve]) -> List[Curve]:
    """Align multiple curves to a common time base via interpolation.

    The output time vector spans the overlapping time range of all
    input curves and uses the highest resolution found.

    Args:
        curves: List of Curve objects with potentially different
            time bases.

    Returns:
        List of new Curve objects with identical time arrays.

    Raises:
        ValueError: If fewer than 2 curves are provided, or if
            there is no overlapping time range.
    """
    if len(curves) < 2:
        raise ValueError("Need at least 2 curves to align.")

    start_time = max(c.time[0] for c in curves)
    end_time = min(c.time[-1] for c in curves)

    if start_time >= end_time:
        raise ValueError(
            "No overlapping time range between curves."
        )

    max_points = max(len(c) for c in curves)
    common_time = np.linspace(start_time, end_time, max_points)

    aligned: List[Curve] = []
    for c in curves:
        new_values = np.interp(common_time, c.time, c.values)
        aligned.append(
            Curve(
                time=common_time,
                values=new_values,
                name=c.name,
                node_id=c.node_id,
                units=c.units,
                metadata=c.metadata.copy(),
                filter_history=list(c.filter_history),
            )
        )

    return aligned


def calculate_rmse(curve_a: Curve, curve_b: Curve) -> float:
    """Calculate Root Mean Square Error between two curves.

    If the curves have different time bases, they are automatically
    aligned first.

    Args:
        curve_a: First curve.
        curve_b: Second curve.

    Returns:
        RMSE value (float).
    """
    if not np.array_equal(curve_a.time, curve_b.time):
        aligned = align_curves([curve_a, curve_b])
        curve_a, curve_b = aligned[0], aligned[1]

    mse = float(np.mean((curve_a.values - curve_b.values) ** 2))
    return float(np.sqrt(mse))


def calculate_difference(
    curve_a: Curve,
    curve_b: Curve,
) -> Curve:
    """Calculate the difference curve (B − A).

    If the curves have different time bases, they are automatically
    aligned first.

    Args:
        curve_a: Baseline curve.
        curve_b: Comparison curve.

    Returns:
        A new Curve representing ``curve_b − curve_a``.
    """
    if not np.array_equal(curve_a.time, curve_b.time):
        aligned = align_curves([curve_a, curve_b])
        curve_a, curve_b = aligned[0], aligned[1]

    diff_values = curve_b.values - curve_a.values
    return Curve(
        time=curve_a.time.copy(),
        values=diff_values,
        name=f"diff({curve_b.name} - {curve_a.name})",
        units=curve_a.units,
    )


def compare_statistics(
    curves: List[Curve],
    labels: List[str] | None = None,
) -> pd.DataFrame:
    """Compare basic statistics across multiple curves.

    Args:
        curves: List of Curve objects.
        labels: Optional human-readable labels for each curve.
            Defaults to each curve's ``name``.

    Returns:
        DataFrame with one row per curve and columns:
        mean, std, min, max, rms, median.
    """
    if labels is None:
        labels = [c.name for c in curves]

    rows = []
    for curve, label in zip(curves, labels):
        stats = basic_statistics(curve)
        stats["label"] = label
        rows.append(stats)

    return pd.DataFrame(rows).set_index("label")
