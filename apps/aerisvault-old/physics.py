"""
AerisVault - Physics & Engineering Calculations
"""

import pandas as pd
from typing import Optional, List

def calculate_derived_channels(
    df: pd.DataFrame, 
    velocity: Optional[float], 
    ref_area: Optional[float], 
    air_density: float = 1.225
) -> pd.DataFrame:
    result_df = df.copy()
    
    if not velocity or velocity <= 0:
        return result_df
        
    q = 0.5 * air_density * (velocity ** 2)
    force_cols = [col for col in df.columns if col.startswith('F')]
    
    for col in force_cols:
        suffix = col[1:] 
        # Cd * S
        result_df[f"CdS_{suffix}"] = result_df[col] / q
        # Cd
        if ref_area and ref_area > 0:
            result_df[f"C_{suffix}"] = result_df[col] / (q * ref_area)
            
    return result_df

def get_available_components(df: pd.DataFrame) -> List[str]:
    return sorted([c for c in df.columns if c != 'time'])