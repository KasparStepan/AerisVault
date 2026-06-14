"""Filesystem paths shared across the portal.

Every module's database and files live under data/<module_key>/. Modules never
hardcode paths — they resolve them through data_dir_for(key).
"""

from pathlib import Path

# Repo root is five parents up from this file:
#   apps/aerisvault/src/aerisvault/shared/paths.py
#   [0] shared  [1] aerisvault  [2] src  [3] apps/aerisvault  [4] apps  [5] AerisVault/
REPO_ROOT = Path(__file__).resolve().parents[5]
DATA_ROOT = REPO_ROOT / "data"


def data_dir_for(module_key: str) -> Path:
    """Return data/<module_key>/, creating it if needed."""
    path = DATA_ROOT / module_key
    path.mkdir(parents=True, exist_ok=True)
    return path
