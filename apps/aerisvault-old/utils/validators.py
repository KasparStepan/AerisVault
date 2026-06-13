"""
AerisVault - Data Validators
Validates dataframe structure and content for physical correctness.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict

class DataValidator:
    """Validates simulation data integrity and physical constraints."""
    
    REQUIRED_COLUMNS = ['time', 'Fpx', 'Fpy', 'Fpz']
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate the structure of the dataframe.
        
        Args:
            df: The dataframe to check
            
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check empty
        if df is None or df.empty:
            return False, ["DataFrame is empty"]
            
        # Check columns
        missing_cols = [col for col in DataValidator.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {', '.join(missing_cols)}")
            
        # Check time monotonicity
        if 'time' in df.columns:
            if not df['time'].is_monotonic_increasing:
                issues.append("Time column is not monotonically increasing")
            if df['time'].isnull().any():
                issues.append("Time column contains NaN values")
                
        return len(issues) == 0, issues

    @staticmethod
    def check_data_quality(df: pd.DataFrame) -> Dict:
        """
        Analyze data quality metrics (completeness, outliers).
        """
        quality = {
            'completeness': {},
            'outliers': {},
            'rows': len(df)
        }
        
        # Check completeness (non-null)
        for col in df.columns:
            non_null = df[col].count()
            quality['completeness'][col] = (non_null / len(df)) * 100
            
        # Simple outlier detection (Z-score > 3)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col == 'time': continue
            
            mean = df[col].mean()
            std = df[col].std()
            
            if std > 0:
                z_scores = np.abs((df[col] - mean) / std)
                outliers = len(df[z_scores > 3])
                quality['outliers'][col] = {
                    'count': outliers,
                    'percentage': (outliers / len(df)) * 100
                }
            else:
                quality['outliers'][col] = {'count': 0, 'percentage': 0.0}
                
        return quality

    @staticmethod
    def validate_physical_constraints(df: pd.DataFrame) -> List[str]:
        """
        Check for physics violations (e.g., negative time).
        """
        violations = []
        
        if 'time' in df.columns and (df['time'] < 0).any():
            violations.append("Negative time values detected")
            
        # Add more constraints as needed
        # e.g., if density is present, it must be > 0
        
        return violations