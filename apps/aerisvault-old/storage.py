"""
AerisVault - File Storage Management
File storage management with compression and format conversion.
"""

import gzip
import json
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime
import pandas as pd

from .models import FileType, StorageFormat
from .parsers import LSDynaICFDDragParser

class StorageManager:
    """Manages physical file storage with format conversion."""
    
    def __init__(self, base_path: str = "data/files"):
        self.base_path = Path(base_path)
        self.keywords_path = self.base_path / "keywords"
        self.results_path = self.base_path / "results"
        
        self.keywords_path.mkdir(parents=True, exist_ok=True)
        self.results_path.mkdir(parents=True, exist_ok=True)
    
    def store_file(
        self,
        file_content: bytes,
        original_filename: str,
        file_type: FileType,
        simulation_id: int
    ) -> Tuple[str, StorageFormat, int, Optional[str]]:
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_name = f"sim{simulation_id}_{timestamp}_{original_filename}"
        
        if file_type == FileType.DRAG_RESULT:
            return self._store_drag_result(file_content, unique_name)
        elif file_type == FileType.KEYWORD:
            return self._store_generic_compressed(file_content, unique_name, self.keywords_path)
        else:
            return self._store_generic_compressed(file_content, unique_name, self.results_path)
    
    def _store_drag_result(self, file_content: bytes, unique_name: str) -> Tuple[str, StorageFormat, int, Optional[str]]:
        try:
            parser = LSDynaICFDDragParser()
            df = parser.parse(file_content)
            
            metadata = parser.extract_metadata(file_content)
            metadata['row_count'] = len(df)
            metadata['time_range'] = [float(df['time'].min()), float(df['time'].max())]
            
            base_name = Path(unique_name).stem
            parquet_name = f"{base_name}.parquet"
            storage_path = self.results_path / parquet_name
            
            df.to_parquet(storage_path, engine='pyarrow', compression='snappy', index=False)
            
            file_size = storage_path.stat().st_size
            relative_path = str(storage_path.relative_to(self.base_path))
            
            return (relative_path, StorageFormat.PARQUET, file_size, json.dumps(metadata))
        
        except Exception as e:
            raise ValueError(f"Failed to store drag result: {str(e)}")
    
    def _store_generic_compressed(self, file_content: bytes, unique_name: str, folder: Path) -> Tuple[str, StorageFormat, int, Optional[str]]:
        gz_name = f"{unique_name}.gz"
        storage_path = folder / gz_name
        
        with gzip.open(storage_path, 'wb') as f:
            f.write(file_content)
        
        file_size = storage_path.stat().st_size
        relative_path = str(storage_path.relative_to(self.base_path))
        
        return (relative_path, StorageFormat.GZIP, file_size, None)
    
    def load_result_data(self, storage_path: str) -> pd.DataFrame:
        full_path = self.base_path / storage_path
        if storage_path.endswith('.parquet'):
            return pd.read_parquet(full_path, engine='pyarrow')
        raise ValueError(f"Unsupported result format: {storage_path}")
    
    def delete_file(self, storage_path: str) -> None:
        full_path = self.base_path / storage_path
        if full_path.exists():
            full_path.unlink()
            
    def get_usage_stats(self) -> dict:
        total_size = sum(f.stat().st_size for f in self.base_path.rglob('*') if f.is_file())
        return {'total_size_mb': total_size / (1024 * 1024)}