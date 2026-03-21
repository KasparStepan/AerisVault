"""Statistical analysis for LS-DYNA time-series data.

Provides basic statistics, peak detection, settling time analysis,
FFT frequency analysis, and time-windowed statistics — all operating
on ``Curve`` objects.
"""

import logging
from typing import Dict, List, Optional

import numpy as np

from dynaprocessing.models.curve import Curve

logger = logging.getLogger(__name__)


def basic_statistics(curve: Curve) -> Dict[str, float]:
    """Calculate basic descriptive statistics for a Curve.

    Args:
        curve: Input curve to analyse.

    Returns:
        Dictionary with keys: mean, std, min, max, rms, median.
    """
    v = curve.values
    return {
        "mean": float(np.mean(v)),
        "std": float(np.std(v)),
        "min": float(np.min(v)),
        "max": float(np.max(v)),
        "rms": float(np.sqrt(np.mean(v ** 2))),
        "median": float(np.median(v)),
    }


def peak_detection(
    curve: Curve,
    prominence: float = 0.1,
    distance: int = 10,
) -> Dict:
    """Detect peaks in the curve signal.

    Args:
        curve: Input curve.
        prominence: Required prominence as a fraction of the data range.
        distance: Minimum sample distance between peaks.

    Returns:
        Dictionary with peak_times, peak_values, num_peaks, prominences.
    """
    from scipy import signal

    data = curve.values
    time = curve.time

    data_range = float(data.max() - data.min())
    prom_val = prominence * data_range if data_range > 0 else 0.1

    peaks, properties = signal.find_peaks(
        data, prominence=prom_val, distance=distance
    )

    return {
        "peak_indices": peaks.tolist(),
        "peak_times": time[peaks].tolist() if len(peaks) > 0 else [],
        "peak_values": data[peaks].tolist() if len(peaks) > 0 else [],
        "num_peaks": len(peaks),
        "prominences": (
            properties.get("prominences", np.array([])).tolist()
        ),
    }


def settling_time(
    curve: Curve,
    tolerance: float = 0.05,
    reference_window: float = 0.1,
) -> Dict:
    """Calculate when the signal settles within a tolerance band.

    Uses the last ``reference_window`` fraction of the data as the
    steady-state reference.

    Args:
        curve: Input curve.
        tolerance: Fraction of the steady-state value used as the
            tolerance band.
        reference_window: Fraction of data from the end to compute the
            reference value.

    Returns:
        Dictionary with settling_time, settling_value, settled (bool).
    """
    data = curve.values
    time = curve.time

    ref_start = int((1.0 - reference_window) * len(data))
    steady_value = float(np.mean(data[ref_start:]))

    tol_band = abs(steady_value * tolerance) if steady_value != 0 else tolerance
    within = np.abs(data - steady_value) <= tol_band

    settling_idx = None
    for i in range(len(within)):
        if np.all(within[i:]):
            settling_idx = i
            break

    if settling_idx is not None:
        return {
            "settling_time": float(time[settling_idx]),
            "settling_value": steady_value,
            "settled": True,
        }
    return {
        "settling_time": None,
        "settling_value": steady_value,
        "settled": False,
    }


def frequency_analysis(
    curve: Curve,
    num_frequencies: int = 5,
) -> Dict:
    """Perform FFT frequency analysis on the curve.

    Args:
        curve: Input curve.
        num_frequencies: Number of dominant frequencies to return.

    Returns:
        Dictionary with sampling_frequency, nyquist_frequency,
        dominant_frequencies, dominant_magnitudes, all_frequencies,
        all_magnitudes.
    """
    data = curve.values
    time = curve.time

    dt = float(np.mean(np.diff(time)))
    fs = 1.0 / dt if dt > 0 else 1.0

    data_centered = data - np.mean(data)

    n = len(data_centered)
    fft_values = np.fft.rfft(data_centered)
    fft_freqs = np.fft.rfftfreq(n, dt)
    fft_magnitude = np.abs(fft_values)

    if len(fft_magnitude) > 1:
        sorted_indices = np.argsort(fft_magnitude[1:])[::-1] + 1
        top_indices = sorted_indices[:num_frequencies]
        dominant_freqs = fft_freqs[top_indices].tolist()
        dominant_mags = fft_magnitude[top_indices].tolist()
    else:
        dominant_freqs = []
        dominant_mags = []

    return {
        "sampling_frequency": fs,
        "nyquist_frequency": fs / 2.0,
        "dominant_frequencies": dominant_freqs,
        "dominant_magnitudes": dominant_mags,
    }


def time_window_statistics(
    curve: Curve,
    start_time: float,
    end_time: float,
) -> Dict[str, float]:
    """Calculate statistics for a specific time window.

    Args:
        curve: Input curve.
        start_time: Window start time (inclusive).
        end_time: Window end time (inclusive).

    Returns:
        Dictionary with the same keys as ``basic_statistics``.

    Raises:
        ValueError: If the window contains no data points.
    """
    mask = (curve.time >= start_time) & (curve.time <= end_time)
    if not np.any(mask):
        raise ValueError(
            f"No data points in window [{start_time}, {end_time}]."
        )

    windowed = Curve(
        time=curve.time[mask],
        values=curve.values[mask],
        name=curve.name,
        node_id=curve.node_id,
        units=curve.units,
    )
    return basic_statistics(windowed)


def correlation_matrix(curves: List[Curve]) -> np.ndarray:
    """Calculate correlation matrix between multiple Curves.

    All curves must have the same length. If they have different time
    bases, align them first using ``comparison.align_curves()``.

    Args:
        curves: List of Curve objects.

    Returns:
        2-D NumPy correlation matrix (N×N).

    Raises:
        ValueError: If curves have different lengths.
    """
    if not curves:
        return np.array([])

    n = len(curves[0])
    for c in curves:
        if len(c) != n:
            raise ValueError(
                "All curves must have the same number of points "
                "for correlation. Use align_curves() first."
            )

    data_matrix = np.column_stack([c.values for c in curves])
    return np.corrcoef(data_matrix, rowvar=False)
