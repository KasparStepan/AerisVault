"""Lazy initialization of the aerocfd module's session-state objects.

All keys are namespaced with the module key ("aerocfd.*") so this module cannot
collide with other modules' session state. Called at the top of every aerocfd page.
"""

import streamlit as st

from aerisvault.modules.aerocfd.core.database import AeroCfdDatabase
from aerisvault.shared.paths import data_dir_for

DB_NAME = "aerocfd.db"


def ensure_initialized() -> None:
    """Create the aerocfd DB once per session, under data/aerocfd/, namespaced."""
    if "aerocfd.db" not in st.session_state:
        aerocfd_dir = data_dir_for("aerocfd")
        st.session_state["aerocfd.db"] = AeroCfdDatabase(
            f"sqlite:///{aerocfd_dir / DB_NAME}"
        )
