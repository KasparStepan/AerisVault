"""
AerisVault - Comparison Page
"""

import streamlit as st
import pandas as pd
from aerisvault.database import DatabaseManager
from aerisvault.storage import StorageManager
from aerisvault.models import FileType
from aerisvault.plotting.comparison_plot import ComparisonPlotter
from aerisvault.analysis.comparison import SimulationComparator

st.set_page_config(page_title="Comparison", page_icon="🔀", layout="wide")

db = DatabaseManager()
storage = StorageManager()
plotter = ComparisonPlotter()
comparator = SimulationComparator()

st.title("🔀 Simulation Comparison")

sims = db.list_simulations()
sims_with_results = [s for s in sims if any(f.file_type == FileType.DRAG_RESULT for f in db.get_files_by_simulation(s.id))]

if len(sims_with_results) < 2:
    st.info("Need at least 2 simulations with result files in the database to compare.")
else:
    selected_sims = st.multiselect(
        "Select Simulations to Compare",
        [s.name for s in sims_with_results],
        default=[s.name for s in sims_with_results[:2]]
    )
    
    if len(selected_sims) >= 2:
        dfs = []
        labels = []
        
        for name in selected_sims:
            sim = next(s for s in sims_with_results if s.name == name)
            files = db.get_files_by_simulation(sim.id)
            res_file = next(f for f in files if f.file_type == FileType.DRAG_RESULT)
            try:
                df = storage.load_result_data(res_file.storage_path)
                dfs.append(df)
                labels.append(name)
            except Exception as e:
                st.error(f"Error loading {name}: {e}")
        
        if len(dfs) == len(selected_sims):
            tab1, tab2 = st.tabs(["📈 Overlay", "📉 Differences"])
            
            with tab1:
                col = st.selectbox("Column", ['Fpz', 'Fpx', 'Fpy'])
                fig = plotter.plot_overlay(dfs, labels, col)
                st.plotly_chart(fig, use_container_width=True)
                
                stats = comparator.compare_statistics(dfs, labels, col)
                st.dataframe(stats)
            
            with tab2:
                if len(dfs) == 2:
                    st.subheader(f"Difference: {labels[1]} - {labels[0]}")
                    col = st.selectbox("Diff Column", ['Fpz', 'Fpx'])
                    fig = plotter.plot_difference(dfs[0], dfs[1], labels[0], labels[1], col)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Difference plot available for exactly 2 simulations.")