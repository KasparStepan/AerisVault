"""
AerisVault - Data Export Utilities
Export data to various formats.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime


class DataExporter:
    """Export simulation data to various formats."""
    
    @staticmethod
    def to_csv(
        df: pd.DataFrame,
        filepath: Path,
        include_metadata: bool = True,
        metadata: Optional[Dict] = None
    ):
        """
        Export DataFrame to CSV.
        
        Args:
            df: DataFrame to export
            filepath: Output file path
            include_metadata: Include metadata as comments
            metadata: Optional metadata dictionary
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            if include_metadata and metadata:
                f.write(f"# AerisVault Export\n")
                f.write(f"# Export Date: {datetime.now().isoformat()}\n")
                for key, value in metadata.items():
                    f.write(f"# {key}: {value}\n")
                f.write("#\n")
            
            df.to_csv(f, index=False)
    
    @staticmethod
    def to_excel(
        df: pd.DataFrame,
        filepath: Path,
        sheet_name: str = "Data",
        include_statistics: bool = True
    ):
        """
        Export DataFrame to Excel with optional statistics sheet.
        
        Args:
            df: DataFrame to export
            filepath: Output file path
            sheet_name: Name for data sheet
            include_statistics: Add statistics sheet
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            if include_statistics:
                stats = df.describe()
                stats.to_excel(writer, sheet_name="Statistics")
    
    @staticmethod
    def to_matlab(
        df: pd.DataFrame,
        filepath: Path,
        variable_name: str = "data"
    ):
        """
        Export DataFrame to MATLAB .mat file.
        
        Args:
            df: DataFrame to export
            filepath: Output file path
            variable_name: MATLAB variable name
        """
        from scipy.io import savemat
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert DataFrame to dict of arrays
        data_dict = {col: df[col].values for col in df.columns}
        
        savemat(str(filepath), {variable_name: data_dict})
    
    @staticmethod
    def to_json(
        df: pd.DataFrame,
        filepath: Path,
        orient: str = 'records',
        include_metadata: bool = True,
        metadata: Optional[Dict] = None
    ):
        """
        Export DataFrame to JSON.
        
        Args:
            df: DataFrame to export
            filepath: Output file path
            orient: JSON orientation ('records', 'split', 'index', etc.)
            include_metadata: Include metadata in output
            metadata: Optional metadata dictionary
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        output = {}
        
        if include_metadata:
            output['metadata'] = metadata or {}
            output['metadata']['export_date'] = datetime.now().isoformat()
        
        output['data'] = json.loads(df.to_json(orient=orient))
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
    
    @staticmethod
    def create_analysis_package(
        df: pd.DataFrame,
        output_dir: Path,
        name: str,
        metadata: Optional[Dict] = None,
        include_plots: bool = True
    ):
        """
        Create complete analysis package with data and metadata.
        
        Args:
            df: DataFrame with analysis results
            output_dir: Output directory
            name: Package name
            metadata: Analysis metadata
            include_plots: Include plot exports
        """
        output_dir = Path(output_dir) / name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export data in multiple formats
        DataExporter.to_csv(df, output_dir / f"{name}.csv", metadata=metadata)
        DataExporter.to_excel(df, output_dir / f"{name}.xlsx")
        DataExporter.to_json(df, output_dir / f"{name}.json", metadata=metadata)
        
        # Save metadata separately
        if metadata:
            with open(output_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
        
        # Create README
        readme_content = f"""# {name} - AerisVault Analysis Package

Export Date: {datetime.now().isoformat()}

## Contents
- {name}.csv - Data in CSV format
- {name}.xlsx - Data in Excel format (with statistics)
- {name}.json - Data in JSON format
- metadata.json - Analysis metadata

## Data Description
Rows: {len(df)}
Columns: {len(df.columns)}

Columns: {', '.join(df.columns)}
"""
        
        with open(output_dir / "README.md", 'w') as f:
            f.write(readme_content)
