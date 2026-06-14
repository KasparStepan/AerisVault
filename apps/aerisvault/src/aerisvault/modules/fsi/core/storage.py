"""
AerisVault UI - Storage Manager
Handles file storage, compression, and conversion (Parquet).
Delegates parsing to dynaprocessing library.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from .models import FileType

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages physical file storage and conversion."""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        (self.base_dir / "raw").mkdir(exist_ok=True)
        (self.base_dir / "processed").mkdir(exist_ok=True)

    def store_file(
        self,
        content: bytes,
        filename: str,
        file_type: FileType,
        sim_id: int,
    ) -> Tuple[str, str, int, Optional[str]]:
        """Store a file and return (storage_path, format, size, metadata)."""
        
        # Save raw file first
        raw_dir = self.base_dir / "raw" / f"sim_{sim_id}"
        raw_dir.mkdir(exist_ok=True, parents=True)
        raw_path = raw_dir / filename
        
        with open(raw_path, "wb") as f:
            f.write(content)
            
        size = len(content)
        fmt = filename.split(".")[-1].lower() if "." in filename else "bin"
        
        # If it's a drag result, try converting to Parquet for performance
        storage_path = str(raw_path)
        metadata = None
        
        if file_type == FileType.DRAG_RESULT and fmt in ["dat", "csv", "txt"]:
            try:
                # Use dynaprocessing to parse (this ensures compatibility)
                from dynaprocessing.io.lsdyna_csv import parse_infinite_mass_dat
                
                # We need to save to a temp file or read from the raw path
                curves = parse_infinite_mass_dat(raw_path)
                
                if curves:
                    # Convert to DataFrame
                    from dynaprocessing.models.curve import Curve
                    df = pd.DataFrame({
                        "time": curves[0].time
                    })
                    for c in curves:
                        df[c.name] = c.values
                    
                    processed_dir = self.base_dir / "processed" / f"sim_{sim_id}"
                    processed_dir.mkdir(exist_ok=True, parents=True)
                    parquet_name = filename.rsplit(".", 1)[0] + ".parquet"
                    parquet_path = processed_dir / parquet_name
                    
                    df.to_parquet(parquet_path)
                    storage_path = str(parquet_path)
                    fmt = "parquet"
                    
                    metadata = f"Columns: {', '.join(df.columns)}"
                    
            except Exception as e:
                logger.warning(f"Could not convert {filename} to Parquet: {e}")
                # Fallback to raw path

        return storage_path, fmt, size, metadata

    def delete_file(self, storage_path: str):
        """Delete file from disk."""
        try:
            p = Path(storage_path)
            if p.exists():
                p.unlink()
        except Exception as e:
            logger.error(f"Error deleting file {storage_path}: {e}")

    def get_full_path(self, relative_path: str) -> Path:
        return Path(relative_path)
