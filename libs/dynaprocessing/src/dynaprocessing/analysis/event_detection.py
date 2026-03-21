"""Event detection for parachute simulation data.

Automatically detects deployment initiation, inflation phases,
steady-state conditions, and oscillatory behaviour from force/
acceleration ``Curve`` objects.
"""

import logging
from typing import Dict

import numpy as np

from dynaprocessing.models.curve import Curve

logger = logging.getLogger(__name__)


def detect_deployment(
    curve: Curve,
    threshold_factor: float = 0.1,
) -> Dict:
    """Detect deployment initiation from a force curve.

    Deployment is defined as the first time the absolute force exceeds
    ``threshold_factor × max(|force|)``.

    Args:
        curve: Force or acceleration curve.
        threshold_factor: Threshold as fraction of peak absolute value.

    Returns:
        Dictionary with detected (bool), deployment_time, deployment_force.
    """
    force = np.abs(curve.values)
    time = curve.time

    threshold = threshold_factor * force.max()
    indices = np.where(force > threshold)[0]

    if len(indices) > 0:
        idx = indices[0]
        return {
            "detected": True,
            "deployment_time": float(time[idx]),
            "deployment_force": float(curve.values[idx]),
            "deployment_index": int(idx),
        }
    return {"detected": False}


def detect_inflation_phases(curve: Curve) -> Dict:
    """Detect inflation phases from the force profile.

    Identifies start, peak, and end of inflation based on force
    magnitude and its rate of change.

    Args:
        curve: Force curve (typically Fpz).

    Returns:
        Dictionary with start_time, peak_time, end_time,
        inflation_duration, peak_force.
    """
    from scipy import signal

    force = np.abs(curve.values)
    time = curve.time

    # Smooth for phase detection
    wl = min(51, len(force))
    if wl % 2 == 0:
        wl -= 1
    wl = max(wl, 3)
    force_smooth = signal.savgol_filter(force, wl, min(3, wl - 1))

    # Force rate of change
    force_rate = np.gradient(force_smooth, time)

    # Peak force
    peak_idx = int(np.argmax(force_smooth))
    peak_time = float(time[peak_idx])
    peak_force = float(force[peak_idx])

    # Start of inflation
    threshold = 0.1 * peak_force
    start_candidates = np.where(force > threshold)[0]
    start_idx = int(start_candidates[0]) if len(start_candidates) > 0 else 0
    start_time = float(time[start_idx])

    # End of inflation (rate stabilises)
    after_peak = force_rate[peak_idx:]
    max_rate = np.max(np.abs(force_rate))
    stable_mask = np.abs(after_peak) < 0.01 * max_rate if max_rate > 0 else np.ones(len(after_peak), dtype=bool)
    stable_indices = np.where(stable_mask)[0]

    if len(stable_indices) > 0:
        end_idx = peak_idx + int(stable_indices[0])
        end_time = float(time[end_idx])
    else:
        end_idx = len(time) - 1
        end_time = float(time[-1])

    return {
        "start_time": start_time,
        "peak_time": peak_time,
        "end_time": end_time,
        "inflation_duration": end_time - start_time,
        "peak_force": peak_force,
        "start_index": start_idx,
        "peak_index": peak_idx,
        "end_index": end_idx,
    }


def detect_steady_state(
    curve: Curve,
    tolerance: float = 0.05,
    window: int = 50,
) -> Dict:
    """Detect when the signal reaches steady state.

    Uses the last 10 % of data as a reference and checks when the
    signal first remains within tolerance for ``window`` consecutive
    samples.

    Args:
        curve: Input curve.
        tolerance: Fractional tolerance band around the steady value.
        window: Number of consecutive samples required within tolerance.

    Returns:
        Dictionary with detected (bool), steady_time, steady_value.
    """
    data = curve.values
    time = curve.time

    ref_idx = int(0.9 * len(data))
    steady_value = float(np.mean(data[ref_idx:]))

    tol_band = abs(steady_value * tolerance) if steady_value != 0 else tolerance
    in_tolerance = np.abs(data - steady_value) <= tol_band

    # Sliding window check
    effective_window = min(window, len(in_tolerance))
    for i in range(len(in_tolerance) - effective_window + 1):
        if np.all(in_tolerance[i : i + effective_window]):
            return {
                "detected": True,
                "steady_time": float(time[i]),
                "steady_value": steady_value,
                "steady_index": i,
            }

    return {
        "detected": False,
        "steady_value": steady_value,
    }


def detect_oscillations(
    curve: Curve,
    min_frequency: float = 0.1,
    max_frequency: float = 10.0,
) -> Dict:
    """Detect oscillations using FFT analysis.

    Args:
        curve: Input curve.
        min_frequency: Minimum oscillation frequency (Hz).
        max_frequency: Maximum oscillation frequency (Hz).

    Returns:
        Dictionary with oscillating (bool), dominant_frequency,
        period, amplitude, fft_magnitude.
    """
    data = curve.values
    time = curve.time

    dt = float(np.mean(np.diff(time)))
    if dt <= 0:
        return {"oscillating": False}

    n = len(data)
    fft_values = np.fft.fft(data)
    fft_freq = np.fft.fftfreq(n, dt)

    freq_mask = (fft_freq >= min_frequency) & (fft_freq <= max_frequency)
    fft_freq_filtered = fft_freq[freq_mask]
    fft_mag_filtered = np.abs(fft_values[freq_mask])

    if len(fft_mag_filtered) > 0:
        dom_idx = int(np.argmax(fft_mag_filtered))
        dom_freq = abs(float(fft_freq_filtered[dom_idx]))
        dom_mag = float(fft_mag_filtered[dom_idx])
        amplitude = float((data.max() - data.min()) / 2.0)

        return {
            "oscillating": True,
            "dominant_frequency": dom_freq,
            "period": 1.0 / dom_freq if dom_freq > 0 else float("inf"),
            "amplitude": amplitude,
            "fft_magnitude": dom_mag,
        }

    return {"oscillating": False}


def auto_detect_events(curve: Curve) -> Dict:
    """Run all event detectors on a single curve.

    Args:
        curve: Force or acceleration curve to analyse.

    Returns:
        Dictionary with keys: deployment, inflation, steady_state,
        oscillations — each containing the respective detector output.
    """
    return {
        "deployment": detect_deployment(curve),
        "inflation": detect_inflation_phases(curve),
        "steady_state": detect_steady_state(curve),
        "oscillations": detect_oscillations(curve),
    }
