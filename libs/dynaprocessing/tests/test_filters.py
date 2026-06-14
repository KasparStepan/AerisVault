"""Tests for digital signal filters."""

import numpy as np
import pytest

from dynaprocessing.analysis.filters import (
    apply_butterworth_filter,
    apply_cfc_filter,
    apply_moving_average_filter,
    get_sampling_frequency,
)


# ---------------------------------------------------------------------------
# Sampling frequency
# ---------------------------------------------------------------------------

class TestSamplingFrequency:
    def test_uniform_timestep(self):
        t = np.linspace(0, 1, 1001)  # dt = 0.001 → fs = 1000 Hz
        fs = get_sampling_frequency(t)
        assert pytest.approx(fs, rel=1e-3) == 1000.0

    def test_rejects_single_point(self):
        with pytest.raises(ValueError, match="at least 2 points"):
            get_sampling_frequency(np.array([0.0]))

    def test_rejects_non_monotonic(self):
        with pytest.raises(ValueError, match="monotonically increasing"):
            get_sampling_frequency(np.array([1.0, 0.0]))


# ---------------------------------------------------------------------------
# CFC filter
# ---------------------------------------------------------------------------

class TestCFCFilter:
    def test_known_sine_attenuation(self):
        """A 500 Hz sine should be attenuated by CFC-60 (fc ≈ 100 Hz)."""
        fs = 10000  # 10 kHz sampling
        t = np.linspace(0, 1, fs)
        high_freq = np.sin(2 * np.pi * 500 * t)

        filtered = apply_cfc_filter(t, high_freq, cfc=60)

        # The 500 Hz component should be heavily attenuated
        # (skip first/last 5% to avoid filter transient at boundaries)
        n = len(filtered)
        interior = filtered[n // 20 : -n // 20]
        assert np.max(np.abs(interior)) < 0.05

    def test_dc_signal_passes_through(self):
        """A constant (DC) signal should be unaffected by any low-pass."""
        t = np.linspace(0, 1, 1000)
        dc = np.full(1000, 42.0)
        filtered = apply_cfc_filter(t, dc, cfc=60)
        np.testing.assert_allclose(filtered, 42.0, atol=1e-6)

    def test_returns_copy_when_nyquist_exceeded(self):
        """When CFC frequency exceeds Nyquist, return unfiltered copy."""
        t = np.linspace(0, 1, 10)  # fs = ~10 Hz, Nyquist ≈ 5 Hz
        v = np.random.randn(10)
        filtered = apply_cfc_filter(t, v, cfc=60)  # fc ≈ 100 >> 5
        np.testing.assert_array_equal(filtered, v)

    def test_preserves_length(self):
        t = np.linspace(0, 1, 500)
        v = np.random.randn(500)
        filtered = apply_cfc_filter(t, v, cfc=60)
        assert len(filtered) == 500

    def test_matches_second_order_phaseless_butterworth(self):
        """SAE J211 CFC = 2nd-order Butterworth applied forward+backward at fc = CFC*5/3."""
        from scipy import signal

        t = np.linspace(0, 1, 10000)
        x = np.random.RandomState(0).randn(10000)

        out = apply_cfc_filter(t, x, cfc=60)

        # Build the reference from the SAME sampling frequency the implementation
        # derives, so the comparison isolates the filter order, not a cutoff mismatch.
        fc = 60 * (5.0 / 3.0)
        nyq = 0.5 * get_sampling_frequency(t)
        b, a = signal.butter(2, fc / nyq, btype="low", analog=False)
        expected = signal.filtfilt(b, a, x)

        np.testing.assert_allclose(out, expected, rtol=1e-9, atol=1e-12)


# ---------------------------------------------------------------------------
# Butterworth filter
# ---------------------------------------------------------------------------

class TestButterworthFilter:
    def test_low_frequency_passes(self):
        """A 5 Hz sine should pass through a 50 Hz low-pass."""
        fs = 1000
        t = np.linspace(0, 1, fs)
        low_freq = np.sin(2 * np.pi * 5 * t)
        filtered = apply_butterworth_filter(t, low_freq, cutoff_freq=50)
        np.testing.assert_allclose(filtered, low_freq, atol=0.05)

    def test_high_frequency_attenuated(self):
        """A 400 Hz sine should be attenuated by a 50 Hz low-pass."""
        fs = 1000
        t = np.linspace(0, 1, fs)
        high_freq = np.sin(2 * np.pi * 400 * t)
        filtered = apply_butterworth_filter(t, high_freq, cutoff_freq=50)
        assert np.max(np.abs(filtered)) < 0.05


# ---------------------------------------------------------------------------
# Moving average filter
# ---------------------------------------------------------------------------

class TestMovingAverageFilter:
    def test_identity_window_1(self):
        v = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        filtered = apply_moving_average_filter(v, window_size=1)
        np.testing.assert_array_equal(filtered, v)

    def test_smoothing_effect(self):
        v = np.array([0, 10, 0, 10, 0, 10, 0, 10, 0, 10], dtype=float)
        filtered = apply_moving_average_filter(v, window_size=3)
        # After smoothing, the oscillation amplitude should decrease
        assert np.std(filtered) < np.std(v)

    def test_preserves_length(self):
        v = np.random.randn(100)
        filtered = apply_moving_average_filter(v, window_size=5)
        assert len(filtered) == 100

    def test_rejects_zero_window(self):
        with pytest.raises(ValueError, match="at least 1"):
            apply_moving_average_filter(np.array([1.0]), window_size=0)
