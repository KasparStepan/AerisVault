"""
AerisVault - Derivative Calculations
Calculate time derivatives of force and moment data.
"""

import pandas as pd
import numpy as np
from typing import Optional


class DerivativeCalculator:
    """Calculate time derivatives of simulation data."""
    
    @staticmethod
    def first_derivative(
        df: pd.DataFrame,
        column: str,
        smooth: bool = True,
        window: int = 5
    ) -> pd.Series:
        """
        Calculate first derivative (rate of change).
        
        Args:
            df: DataFrame with 'time' column
            column: Column to differentiate
            smooth: Apply smoothing before differentiation
            window: Smoothing window size
            
        Returns:
            First derivative series
        """
        time = df['time'].values
        data = df[column].values
        
        if smooth:
            # Smooth data first
            data = pd.Series(data).rolling(window, center=True, min_periods=1).mean().values
        
        # Calculate derivative
        derivative = np.gradient(data, time)
        
        return pd.Series(derivative, index=df.index, name=f'd{column}_dt')
    
    @staticmethod
    def second_derivative(
        df: pd.DataFrame,
        column: str,
        smooth: bool = True,
        window: int = 5
    ) -> pd.Series:
        """
        Calculate second derivative (acceleration).
        
        Args:
            df: DataFrame with 'time' column
            column: Column to differentiate
            smooth: Apply smoothing
            window: Smoothing window size
            
        Returns:
            Second derivative series
        """
        time = df['time'].values
        data = df[column].values
        
        if smooth:
            data = pd.Series(data).rolling(window, center=True, min_periods=1).mean().values
        
        # First derivative
        first_deriv = np.gradient(data, time)
        
        # Second derivative
        second_deriv = np.gradient(first_deriv, time)
        
        return pd.Series(second_deriv, index=df.index, name=f'd2{column}_dt2')
    
    @staticmethod
    def add_derivatives(
        df: pd.DataFrame,
        columns: Optional[list] = None,
        include_second: bool = False
    ) -> pd.DataFrame:
        """
        Add derivative columns to DataFrame.
        
        Args:
            df: Input DataFrame
            columns: Columns to differentiate (default: force/moment columns)
            include_second: Also calculate second derivatives
            
        Returns:
            DataFrame with added derivative columns
        """
        df_with_deriv = df.copy()
        
        if columns is None:
            columns = ['Fpx', 'Fpy', 'Fpz', 'Mpx', 'Mpy', 'Mpz']
            columns = [c for c in columns if c in df.columns]
        
        for col in columns:
            # First derivative
            df_with_deriv[f'd{col}_dt'] = DerivativeCalculator.first_derivative(df, col)
            
            # Second derivative
            if include_second:
                df_with_deriv[f'd2{col}_dt2'] = DerivativeCalculator.second_derivative(df, col)
        
        return df_with_deriv
