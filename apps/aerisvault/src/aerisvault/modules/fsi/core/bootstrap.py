"""Lazy initialization of the FSI module's session-state objects.

All keys are namespaced with the module key ("fsi.*") so this module cannot
collide with other modules' session state. Called at the top of every FSI page.
"""

import streamlit as st

from aerisvault.modules.fsi.core.config import get_settings
from aerisvault.modules.fsi.core.database import SimulationDatabase
from aerisvault.modules.fsi.core.storage import StorageManager
from aerisvault.shared.paths import data_dir_for


def ensure_initialized() -> None:
    """Create the FSI DB, storage, and settings once per session, namespaced."""
    if "fsi.db" not in st.session_state:
        fsi_dir = data_dir_for("fsi")
        settings = get_settings()
        st.session_state["fsi.db"] = SimulationDatabase(
            f"sqlite:///{fsi_dir / settings.db_name}"
        )
        st.session_state["fsi.storage"] = StorageManager(str(fsi_dir))
        st.session_state["fsi.settings"] = settings
