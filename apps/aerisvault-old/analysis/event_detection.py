"""
AerisVault - Event Detection
Automatic detection of deployment, inflation, and other events.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from scipy import signal


class EventDetector:
    """Detect important events in parachute simulation data."""
    
    @staticmethod
    def detect_deployment(
        df: pd.DataFrame,
        force_column: str = 'Fpz',
        threshold_factor: float = 0.1
    ) -> Dict:
        """
        Detect deployment initiation.
        
        Args:
            df: DataFrame with time and force data
            force_column: Column containing deployment force
            threshold_factor: Threshold as fraction of max force
            
        Returns:
            Dictionary with deployment information
        """
        force = df[force_column].abs()
        time = df['time']
        
        # Find threshold crossing
        threshold = threshold_factor * force.max()
        deployment_idx = np.where(force > threshold)[0]
        
        if len(deployment_idx) > 0:
            deployment_time = time.iloc[deployment_idx[0]]
            deployment_force = force.iloc[deployment_idx[0]]
            
            return {
                'detected': True,
                'deployment_time': deployment_time,
                'deployment_force': deployment_force,
                'deployment_index': deployment_idx[0]
            }
        else:
            return {'detected': False}
    
    @staticmethod
    def detect_inflation_phases(
        df: pd.DataFrame,
        force_column: str = 'Fpz'
    ) -> Dict:
        """
        Detect inflation phases based on force profile.
        
        Args:
            df: DataFrame with time and force data
            force_column: Column containing inflation force
            
        Returns:
            Dictionary with phase information
        """
        force = df[force_column].abs()
        time = df['time']
        
        # Smooth force for phase detection
        force_smooth = signal.savgol_filter(force, 51, 3)
        
        # Calculate force derivative
        force_rate = np.gradient(force_smooth, time)
        
        # Find peak force (end of inflation)
        peak_idx = np.argmax(force_smooth)
        peak_time = time.iloc[peak_idx]
        peak_force = force.iloc[peak_idx]
        
        # Find start of inflation (force starts rising)
        threshold = 0.1 * peak_force
        start_candidates = np.where(force > threshold)[0]
        start_idx = start_candidates[0] if len(start_candidates) > 0 else 0
        start_time = time.iloc[start_idx]
        
        # Find end of inflation (force stabilizes)
        # Look for where derivative becomes small
        after_peak = force_rate[peak_idx:]
        stable_idx = peak_idx + np.where(np.abs(after_peak) < 0.01 * np.max(np.abs(force_rate)))[0]
        
        if len(stable_idx) > 0:
            end_idx = stable_idx[0]
            end_time = time.iloc[end_idx]
        else:
            end_idx = len(time) - 1
            end_time = time.iloc[-1]
        
        inflation_time = end_time - start_time
        
        return {
            'start_time': start_time,
            'peak_time': peak_time,
            'end_time': end_time,
            'inflation_duration': inflation_time,
            'peak_force': peak_force,
            'start_index': start_idx,
            'peak_index': peak_idx,
            'end_index': end_idx
        }
    
    @staticmethod
    def detect_steady_state(
        df: pd.DataFrame,
        column: str,
        tolerance: float = 0.05,
        window: int = 50
    ) -> Dict:
        """
        Detect when steady state is reached.
        
        Args:
            df: DataFrame with data
            column: Column to analyze
            tolerance: Variation tolerance (fraction)
            window: Window size for checking stability
            
        Returns:
            Dictionary with steady-state information
        """
        data = df[column]
        time = df['time']
        
        # Use last 10% as steady-state reference
        steady_ref_idx = int(0.9 * len(data))
        steady_value = np.mean(data.iloc[steady_ref_idx:])
        
        threshold = abs(steady_value * tolerance)
        
        # Find where data stays within tolerance
        in_tolerance = np.abs(data - steady_value) <= threshold
        
        for i in range(len(in_tolerance) - window):
            if np.all(in_tolerance.iloc[i:i+window]):
                steady_time = time.iloc[i]
                return {
                    'detected': True,
                    'steady_time': steady_time,
                    'steady_value': steady_value,
                    'steady_index': i
                }
        
        return {
            'detected': False,
            'steady_value': steady_value
        }
    
    @staticmethod
    def detect_oscillations(
        df: pd.DataFrame,
        column: str,
        min_frequency: float = 0.1,
        max_frequency: float = 10.0
    ) -> Dict:
        """
        Detect oscillations in data.
        
        Args:
            df: DataFrame with data
            column: Column to analyze
            min_frequency: Minimum oscillation frequency (Hz)
            max_frequency: Maximum oscillation frequency (Hz)
            
        Returns:
            Dictionary with oscillation information
        """
        data = df[column]
        time = df['time']
        
        # Calculate sampling rate
        dt = np.mean(np.diff(time))
        fs = 1.0 / dt
        
        # FFT analysis
        n = len(data)
        fft_values = np.fft.fft(data)
        fft_freq = np.fft.fftfreq(n, dt)
        
        # Filter to frequency range
        freq_mask = (fft_freq >= min_frequency) & (fft_freq <= max_frequency)
        fft_freq_filtered = fft_freq[freq_mask]
        fft_magnitude_filtered = np.abs(fft_values[freq_mask])
        
        if len(fft_magnitude_filtered) > 0:
            dominant_idx = np.argmax(fft_magnitude_filtered)
            dominant_freq = fft_freq_filtered[dominant_idx]
            dominant_magnitude = fft_magnitude_filtered[dominant_idx]
            
            # Calculate amplitude from data
            amplitude = (data.max() - data.min()) / 2.0
            
            return {
                'oscillating': True,
                'dominant_frequency': abs(dominant_freq),
                'period': 1.0 / abs(dominant_freq),
                'amplitude': amplitude,
                'fft_magnitude': dominant_magnitude
            }
        else:
            return {'oscillating': False}
    
    @staticmethod
    def auto_detect_events(
        df: pd.DataFrame,
        force_column: str = 'Fpz'
    ) -> Dict:
        """
        Automatically detect all major events.
        
        Args:
            df: DataFrame with simulation data
            force_column: Column to use for event detection
            
        Returns:
            Dictionary with all detected events
        """
        deployment = EventDetector.detect_deployment(df, force_column)
        inflation = EventDetector.detect_inflation_phases(df, force_column)
        steady_state = EventDetector.detect_steady_state(df, force_column)
        oscillations = EventDetector.detect_oscillations(df, force_column)
        
        return {
            'deployment': deployment,
            'inflation': inflation,
            'steady_state': steady_state,
            'oscillations': oscillations
        }
