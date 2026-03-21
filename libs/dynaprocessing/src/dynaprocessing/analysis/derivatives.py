"""Time-derivative calculations for LS-DYNA curves.

Compute first and second derivatives of ``Curve`` objects,
optionally with smoothing. All functions return **new** Curve
instances.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from dynaprocessing.models.curve import Curve

logger = logging.getLogger(__name__)


def first_derivative(
    curve: Curve,
    smooth: bool = False,
    window: int = 5,
) -> Curve:
    """Calculate the first time-derivative of a Curve.

    Args:
        curve: Input curve.
        smooth: If True, apply a moving-average smooth before
            differentiation to reduce noise amplification.
        window: Smoothing window size (only used when *smooth* is True).

    Returns:
        A new Curve representing d(values)/dt.
    """
    data = curve.values.copy()

    if smooth:
        kernel = np.ones(window) / float(window)
        data = np.convolve(data, kernel, mode="same")

    derivative = np.gradient(data, curve.time)

    unit_str = f"d({curve.units})/dt" if curve.units else None
    return Curve(
        time=curve.time.copy(),
        values=derivative,
        name=f"d{curve.name}_dt",
        node_id=curve.node_id,
        units=unit_str,
        metadata=curve.metadata.copy(),
        filter_history=list(curve.filter_history) + [
            f"derivative(order=1, smooth={smooth})"
        ],
    )


def second_derivative(
    curve: Curve,
    smooth: bool = False,
    window: int = 5,
) -> Curve:
    """Calculate the second time-derivative of a Curve.

    Args:
        curve: Input curve.
        smooth: If True, apply smoothing before differentiation.
        window: Smoothing window size.

    Returns:
        A new Curve representing d²(values)/dt².
    """
    data = curve.values.copy()

    if smooth:
        kernel = np.ones(window) / float(window)
        data = np.convolve(data, kernel, mode="same")

    d1 = np.gradient(data, curve.time)
    d2 = np.gradient(d1, curve.time)

    unit_str = f"d²({curve.units})/dt²" if curve.units else None
    return Curve(
        time=curve.time.copy(),
        values=d2,
        name=f"d2{curve.name}_dt2",
        node_id=curve.node_id,
        units=unit_str,
        metadata=curve.metadata.copy(),
        filter_history=list(curve.filter_history) + [
            f"derivative(order=2, smooth={smooth})"
        ],
    )
