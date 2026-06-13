"""
AerisVault - File Management Utilities
Handle file operations and organization.
"""

from pathlib import Path
import hashlib
from typing import Optional, Tuple
import shutil


class FileManager:
    """Manage file operations for AerisVault."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize file manager."""
        if base_dir is None:
            base_dir = Path.home() / ".aerisvault" / "uploads"
        
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_uploaded_file(
        self,
        file_content: bytes,
        original_filename: str,
        project_id: Optional[int] = None
    ) -> Tuple[Path, str]:
        """
        Save uploaded file and return path and hash.
        
        Args:
            file_content: File content as bytes
            original_filename: Original filename
            project_id: Optional project ID for organization
            
        Returns:
            Tuple of (file_path, file_hash)
        """
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()[:16]
        
        # Determine save location
        if project_id is not None:
            save_dir = self.base_dir / f"project_{project_id}"
        else:
            save_dir = self.base_dir / "unorganized"
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with hash to avoid collisions
        file_extension = Path(original_filename).suffix
        save_filename = f"{file_hash}_{original_filename}"
        save_path = save_dir / save_filename
        
        # Save file
        with open(save_path, 'wb') as f:
            f.write(file_content)
        
        return save_path, file_hash
    
    def get_file_path(self, file_hash: str) -> Optional[Path]:
        """Find file by hash."""
        for file_path in self.base_dir.rglob(f"{file_hash}_*"):
            return file_path
        return None
    
    def delete_file(self, file_hash: str) -> bool:
        """Delete file by hash."""
        file_path = self.get_file_path(file_hash)
        if file_path and file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def organize_by_project(self, file_hash: str, project_id: int) -> bool:
        """Move file to project directory."""
        current_path = self.get_file_path(file_hash)
        if not current_path:
            return False
        
        project_dir = self.base_dir / f"project_{project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        new_path = project_dir / current_path.name
        shutil.move(str(current_path), str(new_path))
        
        return True
    
    def get_storage_usage(self) -> dict:
        """Get storage statistics."""
        total_size = 0
        file_count = 0
        
        for file_path in self.base_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'file_count': file_count
        }
