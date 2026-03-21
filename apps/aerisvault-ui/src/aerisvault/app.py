"""
AerisVault - Thin UI Shell
Main application entry point.
"""

import streamlit as st
from aerisvault.core.config import get_settings
from aerisvault.core.database import SimulationDatabase
from aerisvault.core.storage import StorageManager


def main():
    st.set_page_config(
        page_title="AerisVault",
        page_icon="🪂",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize managers and store in session state
    if "db" not in st.session_state:
        settings = get_settings()
        st.session_state.db = SimulationDatabase(f"sqlite:///{settings.db_name}")
        st.session_state.storage = StorageManager(settings.data_dir)
        st.session_state.settings = settings

    # Sidebar Navigation
    st.sidebar.title("🪂 AerisVault")
    st.sidebar.markdown("---")
    
    # Simple Dashboard Overview in Sidebar
    sims = st.session_state.db.list_simulations()
    st.sidebar.metric("Simulations", len(sims))
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**AerisVault v0.3.0**\n\n"
        "Advanced Post-processing for LS-DYNA ICFD simulations."
    )

    # Main Dashboard Page (landing)
    st.title("🚀 AerisVault Dashboard")
    st.markdown("""
    Welcome to **AerisVault**, your central hub for LS-DYNA parachute simulation analysis.
    Use the sidebar to navigate between data management and analysis modules.
    """)

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📁 Database")
        st.write("Browse and manage your simulation registry.")
        if st.button("Go to Database", type="primary"):
            st.switch_page("pages/01_database.py")

    with col2:
        st.subheader("📊 Analysis")
        st.write("Perform detailed analysis on single simulations.")
        if st.button("Go to Analysis", type="primary"):
            st.switch_page("pages/02_single_analysis.py")

    with col3:
        st.subheader("📈 Comparison")
        st.write("Compare multiple simulations side-by-side.")
        if st.button("Go to Comparison", type="primary"):
            st.switch_page("pages/03_comparison.py")

    st.divider()
    
    # Recent Activity / Stats
    st.subheader("📋 Recent Simulations")
    if sims:
        import pandas as pd
        recent = sims[:5]
        df = pd.DataFrame([{
            "Name": s.name,
            "Created": s.created_at.strftime("%Y-%m-%d %H:%M"),
            "Files": len(st.session_state.db.get_files_by_simulation(s.id))
        } for s in recent])
        st.table(df)
    else:
        st.info("No simulations in the database yet. Go to Database to add one.")


if __name__ == "__main__":
    main()
