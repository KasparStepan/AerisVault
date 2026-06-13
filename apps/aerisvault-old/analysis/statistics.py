"""
AerisVault - Statistical Analysis
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict
from scipy import signal


class StatisticalAnalyzer:
    @staticmethod
    def basic_statistics(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Calculate basic statistics for specified columns."""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'time' in columns: columns.remove('time')
        
        stats_list = []
        for col in columns:
            if col in df.columns:
                s = df[col].dropna()
                stats_list.append({
                    'Column': col,
                    'mean': s.mean(),
                    'std': s.std(),
                    'min': s.min(),
                    'max': s.max(),
                    'rms': np.sqrt((s**2).mean())
                })
        return pd.DataFrame(stats_list).set_index('Column')
    
    @staticmethod
    def peak_detection(
        df: pd.DataFrame,
        column: str,
        prominence: float = 0.1,
        distance: int = 10
    ) -> Dict:
        """
        Detect peaks in the data.
        
        Args:
            df: DataFrame with data
            column: Column to analyze
            prominence: Required prominence of peaks (as fraction of range)
            distance: Minimum distance between peaks
            
        Returns:
            Dictionary with peak information
        """
        data = df[column].values
        time = df['time'].values
        
        # Calculate prominence threshold
        data_range = data.max() - data.min()
        prom_val = prominence * data_range if data_range > 0 else 0.1
        
        # Find peaks
        peaks, properties = signal.find_peaks(
            data,
            prominence=prom_val,
            distance=distance
        )
        
        return {
            'peak_indices': peaks.tolist(),
            'peak_times': time[peaks].tolist() if len(peaks) > 0 else [],
            'peak_values': data[peaks].tolist() if len(peaks) > 0 else [],
            'num_peaks': len(peaks),
            'prominences': properties.get('prominences', []).tolist() if 'prominences' in properties else []
        }
    
    @staticmethod
    def settling_time(
        df: pd.DataFrame,
        column: str,
        tolerance: float = 0.05,
        reference_window: float = 0.1
    ) -> Dict:
        """
        Calculate settling time - when signal settles within tolerance of final value.
        
        Args:
            df: DataFrame with data
            column: Column to analyze
            tolerance: Tolerance band (fraction of steady-state value)
            reference_window: Fraction of data to use for steady-state reference
            
        Returns:
            Dictionary with settling time information
        """
        data = df[column].values
        time = df['time'].values
        
        # Use last portion of data as steady-state reference
        ref_start_idx = int((1 - reference_window) * len(data))
        steady_value = np.mean(data[ref_start_idx:])
        
        # Calculate tolerance bounds
        tol_band = abs(steady_value * tolerance) if steady_value != 0 else tolerance
        
        # Find first time data stays within tolerance
        within_tolerance = np.abs(data - steady_value) <= tol_band
        
        # Look for sustained settling (must stay settled)
        settling_idx = None
        for i in range(len(within_tolerance)):
            if np.all(within_tolerance[i:]):
                settling_idx = i
                break
        
        if settling_idx is not None:
            return {
                'settling_time': time[settling_idx],
                'settling_value': steady_value,
                'settled': True,
                'settling_index': settling_idx
            }
        else:
            return {
                'settling_time': None,
                'settling_value': steady_value,
                'settled': False,
                'settling_index': None
            }
    
    @staticmethod
    def frequency_analysis(
        df: pd.DataFrame,
        column: str,
        num_frequencies: int = 5
    ) -> Dict:
        """
        Perform FFT frequency analysis.
        
        Args:
            df: DataFrame with data
            column: Column to analyze
            num_frequencies: Number of dominant frequencies to return
            
        Returns:
            Dictionary with frequency analysis results
        """
        data = df[column].values
        time = df['time'].values
        
        # Calculate sampling frequency
        dt = np.mean(np.diff(time))
        fs = 1.0 / dt if dt > 0 else 1.0
        
        # Remove DC component (mean)
        data_centered = data - np.mean(data)
        
        # Perform FFT
        n = len(data_centered)
        fft_values = np.fft.rfft(data_centered)
        fft_freqs = np.fft.rfftfreq(n, dt)
        fft_magnitude = np.abs(fft_values)
        
        # Get dominant frequencies (skip DC component at index 0)
        if len(fft_magnitude) > 1:
            sorted_indices = np.argsort(fft_magnitude[1:])[::-1] + 1  # +1 to account for skipping DC
            top_indices = sorted_indices[:num_frequencies]
            
            dominant_freqs = fft_freqs[top_indices].tolist()
            dominant_mags = fft_magnitude[top_indices].tolist()
        else:
            dominant_freqs = []
            dominant_mags = []
        
        return {
            'sampling_frequency': fs,
            'nyquist_frequency': fs / 2,
            'dominant_frequencies': dominant_freqs,
            'dominant_magnitudes': dominant_mags,
            'all_frequencies': fft_freqs.tolist(),
            'all_magnitudes': fft_magnitude.tolist()
        }
    
    @staticmethod
    def correlation_matrix(
        df: pd.DataFrame,
        columns: List[str]
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for specified columns.
        
        Args:
            df: DataFrame with data
            columns: Columns to include in correlation
            
        Returns:
            Correlation matrix as DataFrame
        """
        return df[columns].corr()
    
    @staticmethod
    def time_window_statistics(
        df: pd.DataFrame,
        start_time: float,
        end_time: float,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Calculate statistics for a specific time window.
        
        Args:
            df: DataFrame with time series data
            start_time: Start of time window
            end_time: End of time window
            columns: Columns to analyze (default: all numeric except time)
            
        Returns:
            Statistics DataFrame for the time window
        """
        # Filter to time window
        mask = (df['time'] >= start_time) & (df['time'] <= end_time)
        df_window = df[mask]
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'time' in columns:
                columns.remove('time')
        
        return StatisticalAnalyzer.basic_statistics(df_window, columns)