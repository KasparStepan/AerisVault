"""
AerisVault - Main Application Entry Point
"""

import streamlit as st
from pathlib import Path
import sys

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from aerisvault.config import get_settings
from aerisvault.database import DatabaseManager
from aerisvault.storage import StorageManager

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="AerisVault",
    page_icon="🪂",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    settings = get_settings()
    db = DatabaseManager()
    storage = StorageManager(base_path=settings.data_dir)

    st.title("🪂 AerisVault")
    st.subheader("Advanced Analysis for LS-DYNA ICFD")

    # Dashboard Overview
    col1, col2, col3 = st.columns(3)
    
    sims = db.list_simulations()
    sim_count = len(sims)
    
    with col1:
        st.metric("Total Simulations", sim_count)
    
    with col2:
        proj_count = len(db.list_all_tags())
        st.metric("Active Tags", proj_count)
        
    with col3:
        usage = storage.get_usage_stats() if hasattr(storage, 'get_usage_stats') else {'total_size_mb': 0}
        st.metric("Storage Used", f"{usage.get('total_size_mb', 0):.1f} MB")

    st.divider()

    st.markdown("""
    ### 🚀 Getting Started
    
    Use the sidebar to navigate between modules:
    
    * **📊 Single Analysis**: Visualize and analyze individual simulation runs.
    * **🔀 Comparison**: Compare multiple simulations side-by-side.
    * **📁 Database**: Manage simulations, upload files, and organize tags.
    * **⚙️ Settings**: Configure application defaults.
    """)
    
    # Recent Activity
    st.subheader("🕒 Recent Simulations")
    if sims:
        recents = sims[:5]
        for sim in recents:
            with st.expander(f"{sim.name} ({sim.created_at.strftime('%Y-%m-%d')})"):
                st.write(sim.description)
                st.caption(f"Velocity: {sim.velocity} m/s | Area: {sim.ref_area} m²")
    else:
        st.info("No simulations found. Go to 'Database' to upload one.")

if __name__ == "__main__":
    main()