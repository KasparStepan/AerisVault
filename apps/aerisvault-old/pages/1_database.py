"""
AerisVault - Simulation Database
Manage simulations, tags, and organize your results.
"""

import streamlit as st
import sys
from pathlib import Path

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aerisvault.database import SimulationDatabase
from aerisvault.storage import StorageManager
from aerisvault.ui.pages import database_page, manage_database_page

st.set_page_config(page_title="Database", page_icon="🗄️", layout="wide")

# Initialize managers
db = SimulationDatabase()
storage = StorageManager()

st.title("🗄️ Simulation Database")
st.caption("Manage your LS-DYNA ICFD simulation results")

# Use tabs to separate Viewing from Management
tab_view, tab_manage = st.tabs(["📋 Browse Simulations", "✏️ Manage Database"])

with tab_view:
    # Use the refactored page logic from ui/pages.py
    database_page(db, storage)

with tab_manage:
    manage_database_page(db, storage)