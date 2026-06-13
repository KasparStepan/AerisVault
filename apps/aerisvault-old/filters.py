"""
AerisVault - Data Filtering
"""

import numpy as np
import pandas as pd
from scipy import signal
from typing import Literal

class DataFilter:
    @staticmethod
    def savitzky_golay(
        data: pd.Series,
        window_length: int = 51,
        polyorder: int = 3
    ) -> pd.Series:
        """Apply Savitzky-Golay filter."""
        wl = window_length
        if wl % 2 == 0: 
            wl += 1
        wl = min(wl, len(data))
        if wl < 3:
            wl = 3
        po = min(polyorder, wl - 1)
        return pd.Series(signal.savgol_filter(data, wl, po), index=data.index)
    
    @staticmethod
    def moving_average(
        data: pd.Series,
        window: int = 10
    ) -> pd.Series:
        """Apply moving average filter."""
        w = min(window, len(data))
        return data.rolling(window=w, center=True, min_periods=1).mean()
    
    @staticmethod
    def lowpass_butterworth(
        data: pd.Series,
        time: pd.Series,
        cutoff_freq: float = 10.0,
        order: int = 4
    ) -> pd.Series:
        """Apply Butterworth lowpass filter."""
        # Calculate sampling frequency
        dt = np.mean(np.diff(time))
        if dt <= 0:
            return data
        fs = 1.0 / dt
        nyq = 0.5 * fs
        
        # Normalize cutoff frequency
        normalized_cutoff = cutoff_freq / nyq
        
        # Ensure cutoff is valid
        if normalized_cutoff >= 1.0:
            normalized_cutoff = 0.99
        elif normalized_cutoff <= 0:
            normalized_cutoff = 0.01
        
        try:
            b, a = signal.butter(order, normalized_cutoff, btype='low')
            filtered = signal.filtfilt(b, a, data.values)
            return pd.Series(filtered, index=data.index)
        except Exception:
            # Fall back to original data if filter fails
            return data
    
    @staticmethod
    def apply_filter(
        data: pd.Series,
        time: pd.Series,
        filter_type: Literal["savgol", "moving_average", "lowpass"],
        **kwargs
    ) -> pd.Series:
        """Generic filter application method."""
        if filter_type == "savgol":
            wl = kwargs.get('window_length', 51)
            po = kwargs.get('polyorder', 3)
            return DataFilter.savitzky_golay(data, wl, po)
            
        elif filter_type == "moving_average":
            w = kwargs.get('window', 10)
            return DataFilter.moving_average(data, w)
            
        elif filter_type == "lowpass":
            cutoff = kwargs.get('cutoff_freq', 10.0)
            order = kwargs.get('order', 4)
            return DataFilter.lowpass_butterworth(data, time, cutoff, order)
            
        return data