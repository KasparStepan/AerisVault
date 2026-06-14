"""Digital signal filters for LS-DYNA time-series post-processing.

Provides SAE J211 CFC filtering, generic Butterworth low-pass filtering,
and simple moving-average smoothing.

All functions are pure: they accept NumPy arrays and return new arrays
without mutating the inputs.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def get_sampling_frequency(time_array: np.ndarray) -> float:
    """Compute average sampling frequency from a time array.

    Args:
        time_array: Monotonically increasing time stamps.

    Returns:
        Sampling frequency in Hz.

    Raises:
        ValueError: If the array has fewer than 2 points or is not
            monotonically increasing.
    """
    if len(time_array) < 2:
        raise ValueError(
            "Time array must have at least 2 points to determine "
            "sampling frequency."
        )
    dt_mean = float(np.mean(np.diff(time_array)))
    if dt_mean <= 0:
        raise ValueError("Time array must be monotonically increasing.")
    return 1.0 / dt_mean


def apply_cfc_filter(
    time: np.ndarray, data: np.ndarray, cfc: float = 60
) -> np.ndarray:
    """Apply an SAE J211 CFC (Channel Frequency Class) filter.

    The CFC value defines the cut-off frequency as ``fc = cfc * 5/3``.
    Internally uses a 2nd-order Butterworth applied forward and backward
    (``filtfilt``) for zero phase distortion, as specified by SAE J211.

    Args:
        time: Time array for sampling-frequency estimation.
        data: Signal values to filter.
        cfc: Channel Frequency Class (e.g., 60, 180, 600, 1000).

    Returns:
        Filtered signal (same length as *data*).
    """
    from scipy import signal

    fs = get_sampling_frequency(time)
    fc = cfc * (5.0 / 3.0)
    nyq = 0.5 * fs

    if fc >= nyq:
        logger.warning(
            "CFC-%s cut-off (%.1f Hz) exceeds Nyquist (%.1f Hz). "
            "Returning unfiltered data.",
            cfc, fc, nyq,
        )
        return data.copy()

    normal_cutoff = fc / nyq
    # SAE J211 specifies a 2nd-order Butterworth applied forward and backward
    # (filtfilt) for zero phase distortion.
    b, a = signal.butter(2, normal_cutoff, btype="low", analog=False)
    return signal.filtfilt(b, a, data)


def apply_butterworth_filter(
    time: np.ndarray,
    data: np.ndarray,
    cutoff_freq: float,
    order: int = 4,
) -> np.ndarray:
    """Apply a standard Butterworth low-pass filter.

    Args:
        time: Time array for sampling-frequency estimation.
        data: Signal values to filter.
        cutoff_freq: Cut-off frequency in Hz.
        order: Filter order (default 4).

    Returns:
        Filtered signal (same length as *data*).
    """
    from scipy import signal

    fs = get_sampling_frequency(time)
    nyq = 0.5 * fs

    if cutoff_freq >= nyq:
        logger.warning(
            "Butterworth cut-off (%.1f Hz) exceeds Nyquist (%.1f Hz). "
            "Returning unfiltered data.",
            cutoff_freq, nyq,
        )
        return data.copy()

    normal_cutoff = cutoff_freq / nyq
    b, a = signal.butter(order, normal_cutoff, btype="low", analog=False)
    return signal.filtfilt(b, a, data)


def apply_moving_average_filter(
    data: np.ndarray, window_size: int = 5
) -> np.ndarray:
    """Apply a simple moving-average smoothing filter.

    Args:
        data: Signal values to smooth.
        window_size: Number of points in the averaging window.

    Returns:
        Smoothed signal (same length as *data*).

    Raises:
        ValueError: If *window_size* < 1.
    """
    if window_size < 1:
        raise ValueError("Window size must be at least 1.")
    if window_size == 1:
        return data.copy()

    kernel = np.ones(window_size) / float(window_size)
    return np.convolve(data, kernel, mode="same")


def apply_savgol_filter(
    data: np.ndarray,
    window_length: int = 51,
    polyorder: int = 3,
) -> np.ndarray:
    """Apply a Savitzky-Golay smoothing filter.

    Automatically adjusts the window length to be odd and no larger
    than the data length, and clamps the polynomial order accordingly.

    Args:
        data: Signal values to smooth.
        window_length: Number of points in the filter window (must be
            odd; will be adjusted if even).
        polyorder: Polynomial order for the local fit.

    Returns:
        Smoothed signal (same length as *data*).
    """
    from scipy import signal

    wl = window_length
    if wl % 2 == 0:
        wl += 1
    wl = min(wl, len(data))
    if wl < 3:
        wl = 3
    po = min(polyorder, wl - 1)
    return signal.savgol_filter(data, wl, po)
