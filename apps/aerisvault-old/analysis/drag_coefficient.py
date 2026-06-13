"""
AerisVault - Drag Coefficient Calculator
Calculate drag coefficients from force data.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict


class DragCoefficientCalculator:
    """Calculate drag coefficients from simulation data."""
    
    @staticmethod
    def calculate_cd(
        force: pd.Series,
        reference_area: float,
        velocity: float,
        density: float = 1.225
    ) -> pd.Series:
        """
        Calculate drag coefficient from force data.
        
        Cd = F / (0.5 * rho * V^2 * A)
        
        Args:
            force: Force data (N)
            reference_area: Reference area (m²)
            velocity: Velocity (m/s)
            density: Fluid density (kg/m³), default air at sea level
            
        Returns:
            Drag coefficient time series
        """
        dynamic_pressure = 0.5 * density * velocity ** 2
        cd = force / (dynamic_pressure * reference_area)
        return cd
    
    @staticmethod
    def calculate_cd_variable_velocity(
        force: pd.Series,
        velocity: pd.Series,
        reference_area: float,
        density: float = 1.225
    ) -> pd.Series:
        """
        Calculate drag coefficient with variable velocity.
        
        Args:
            force: Force data (N)
            velocity: Velocity data (m/s)
            reference_area: Reference area (m²)
            density: Fluid density (kg/m³)
            
        Returns:
            Drag coefficient time series
        """
        dynamic_pressure = 0.5 * density * velocity ** 2
        cd = force / (dynamic_pressure * reference_area + 1e-10)  # Avoid division by zero
        return cd
    
    @staticmethod
    def reynolds_number(
        velocity: float,
        characteristic_length: float,
        kinematic_viscosity: float = 1.5e-5
    ) -> float:
        """
        Calculate Reynolds number.
        
        Re = V * L / nu
        
        Args:
            velocity: Flow velocity (m/s)
            characteristic_length: Characteristic length (m)
            kinematic_viscosity: Kinematic viscosity (m²/s), default air
            
        Returns:
            Reynolds number
        """
        return velocity * characteristic_length / kinematic_viscosity
    
    @staticmethod
    def analyze_drag_coefficient(
        df: pd.DataFrame,
        force_column: str,
        reference_area: float,
        velocity: float,
        density: float = 1.225
    ) -> Dict:
        """
        Comprehensive drag coefficient analysis.
        
        Args:
            df: DataFrame with force data
            force_column: Name of force column
            reference_area: Reference area (m²)
            velocity: Velocity (m/s)
            density: Fluid density (kg/m³)
            
        Returns:
            Dictionary with Cd statistics and time series
        """
        cd = DragCoefficientCalculator.calculate_cd(
            df[force_column],
            reference_area,
            velocity,
            density
        )
        
        # Calculate steady-state Cd (last 20% of data)
        steady_start = int(0.8 * len(cd))
        cd_steady = cd.iloc[steady_start:]
        
        return {
            'cd_time_series': cd,
            'cd_mean': cd.mean(),
            'cd_std': cd.std(),
            'cd_steady_mean': cd_steady.mean(),
            'cd_steady_std': cd_steady.std(),
            'cd_min': cd.min(),
            'cd_max': cd.max(),
            'dynamic_pressure': 0.5 * density * velocity ** 2,
            'reynolds_number': DragCoefficientCalculator.reynolds_number(
                velocity,
                np.sqrt(reference_area / np.pi) * 2  # Approximate diameter
            )
        }
