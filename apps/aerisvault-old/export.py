"""
AerisVault - Export Utilities
"""
import pandas as pd
from typing import Dict, List, Optional

class DataExporter:
    @staticmethod
    def export_comparison_to_csv(
        data_dict: Dict[str, pd.DataFrame],
        components: Optional[List[str]] = None
    ) -> str:
        if not data_dict: return ""
        
        # Unify time index
        all_times = sorted(set().union(*[df['time'].values for df in data_dict.values()]))
        export_df = pd.DataFrame({'time': all_times})
        
        first_df = list(data_dict.values())[0]
        if components is None:
            components = [c for c in first_df.columns if c != 'time']
            
        for sim_name, df in data_dict.items():
            df_indexed = df.set_index('time')
            # Reindex to master time
            df_reindexed = df_indexed.reindex(all_times).interpolate(method='index')
            
            for col in components:
                if col in df_reindexed.columns:
                    export_df[f"{sim_name}_{col}"] = df_reindexed[col].values
                    
        return export_df.to_csv(index=False)