"""
AerisVault - Simulation Comparator
Logic for comparing multiple simulation datasets.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional

class SimulationComparator:
    """Performs mathematical comparison between simulations."""

    @staticmethod
    def align_time_series(dfs: List[pd.DataFrame]) -> List[pd.DataFrame]:
        """
        Align multiple dataframes to a common time index using interpolation.
        Returns a list of re-indexed dataframes.
        """
        if not dfs:
            return []
            
        # Find global time range bounds
        start_time = max(df['time'].min() for df in dfs)
        end_time = min(df['time'].max() for df in dfs)
        
        # Create common time vector (using the highest sampling rate found)
        max_points = max(len(df) for df in dfs)
        common_time = np.linspace(start_time, end_time, max_points)
        
        aligned_dfs = []
        for df in dfs:
            # Create a new DF for interpolation
            df_new = pd.DataFrame({'time': common_time})
            
            # Interpolate all numeric columns
            for col in df.columns:
                if col != 'time' and pd.api.types.is_numeric_dtype(df[col]):
                    df_new[col] = np.interp(common_time, df['time'], df[col])
            
            aligned_dfs.append(df_new)
            
        return aligned_dfs

    @staticmethod
    def calculate_rmse(df1: pd.DataFrame, df2: pd.DataFrame, columns: List[str]) -> Dict[str, float]:
        """
        Calculate Root Mean Square Error between two simulations.
        """
        # Align first
        aligned = SimulationComparator.align_time_series([df1, df2])
        d1, d2 = aligned[0], aligned[1]
        
        results = {}
        for col in columns:
            if col in d1.columns and col in d2.columns:
                mse = ((d1[col] - d2[col]) ** 2).mean()
                results[col] = np.sqrt(mse)
                
        return results

    @staticmethod
    def calculate_differences(df1: pd.DataFrame, df2: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Return a dataframe containing the differences (df2 - df1).
        """
        aligned = SimulationComparator.align_time_series([df1, df2])
        d1, d2 = aligned[0], aligned[1]
        
        diff_df = pd.DataFrame({'time': d1['time']})
        
        for col in columns:
            if col in d1.columns and col in d2.columns:
                diff_df[f'{col}_diff'] = d2[col] - d1[col]
                # Avoid division by zero for relative diff
                denominator = d1[col].replace(0, np.nan)
                diff_df[f'{col}_rel_diff'] = (diff_df[f'{col}_diff'] / denominator) * 100
                
        return diff_df

    @staticmethod
    def compare_statistics(dfs: List[pd.DataFrame], labels: List[str], column: str) -> pd.DataFrame:
        """
        Compare statistical metrics for a specific column across simulations.
        """
        stats_data = []
        
        for df, label in zip(dfs, labels):
            if column in df.columns:
                series = df[column]
                stats_data.append({
                    'Simulation': label,
                    'mean': series.mean(),
                    'std': series.std(),
                    'min': series.min(),
                    'max': series.max(),
                    'rms': np.sqrt((series ** 2).mean())
                })
                
        return pd.DataFrame(stats_data).set_index('Simulation')

    @staticmethod
    def convergence_analysis(dfs: List[pd.DataFrame], reference_idx: int, columns: List[str]) -> Dict:
        """
        Analyze convergence assuming dfs are ordered by mesh refinement.
        """
        if len(dfs) < 2:
            return {}
            
        ref_df = dfs[reference_idx]
        others = [d for i, d in enumerate(dfs) if i != reference_idx]
        
        convergence_data = {}
        
        for col in columns:
            errors = []
            for other_df in others:
                rmse_dict = SimulationComparator.calculate_rmse(ref_df, other_df, [col])
                errors.append(rmse_dict.get(col, 0.0))
            
            convergence_data[col] = {'errors': errors}
            
        return convergence_data