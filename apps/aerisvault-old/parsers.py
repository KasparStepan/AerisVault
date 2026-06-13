"""
AerisVault - File Parsers
"""

import re
import io
from typing import Dict, Any, Tuple, List
import pandas as pd

class LSDynaICFDDragParser:
    def __init__(self):
        self.expected_columns = [
            "time", "Fpx", "Fpy", "Fpz", "Fvx", "Fvy", "Fvz",
            "Mpx", "Mpy", "Mpz", "Mvx", "Mvy", "Mvz"
        ]
    
    def parse(self, file_content: bytes) -> pd.DataFrame:
        try:
            text = file_content.decode('utf-8', errors='replace')
            lines = text.split('\n')
            
            # Find header
            header_idx = -1
            for i, line in enumerate(lines[:30]):
                if 'time' in line.lower() and ('Fpx' in line or 'fpx' in line.lower()):
                    header_idx = i
                    break
            
            if header_idx == -1:
                raise ValueError("Header not found")
            
            # Extract data
            data_start = header_idx + 1
            while data_start < len(lines) and not lines[data_start].strip():
                data_start += 1
                
            data_lines = [line.strip() for line in lines[data_start:] if line.strip() and (line.strip()[0].isdigit() or line.strip()[0] in '-+')]
            
            if not data_lines:
                raise ValueError("No data found")
                
            df = pd.read_csv(
                io.StringIO('\n'.join(data_lines)),
                delim_whitespace=True,
                header=None,
                names=self.expected_columns,
                on_bad_lines='warn'
            )
            
            # Ensure numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            return df.dropna().sort_values('time').reset_index(drop=True)
            
        except Exception as e:
            raise ValueError(f"Parser error: {str(e)}")
            
    def extract_metadata(self, file_content: bytes) -> Dict[str, Any]:
        return {"parser": "LSDynaICFDDragParser"}