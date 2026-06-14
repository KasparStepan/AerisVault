"""
AerisVault UI - Settings Page
Configure application-wide defaults.
"""

import streamlit as st
from aerisvault.modules.fsi.core.config import get_settings
from aerisvault.modules.fsi.core.bootstrap import ensure_initialized


def render():
    ensure_initialized()
    settings = st.session_state["fsi.settings"]

    st.title("⚙️ Application Settings")

    with st.form("settings_form"):
        st.subheader("📂 Directory Settings")
        new_data_dir = st.text_input("Data Root Directory", value=settings.data_dir)
        new_db_name = st.text_input("Database Filename", value=settings.db_name)

        st.divider()

        st.subheader("🔧 Default Filter Defaults")
        f_settings = settings.filter_settings

        new_enabled = st.checkbox("Enable Filtering by Default", value=f_settings.enabled_by_default)
        new_filter_type = st.selectbox(
            "Default Filter Type",
            ["cfc", "butterworth", "moving_average", "savgol"],
            index=["cfc", "butterworth", "moving_average", "savgol"].index(f_settings.default_filter_type)
        )

        col1, col2 = st.columns(2)
        new_cfc = col1.select_slider("Default CFC Class", options=[60, 180, 600, 1000], value=f_settings.cfc_class)
        new_cutoff = col2.number_input("Default Cutoff (Hz)", value=f_settings.lowpass_cutoff_freq)

        st.divider()

        st.subheader("📊 Plot defaults")
        p_settings = settings.plot_settings
        new_theme = st.selectbox("Plotly Theme", ["plotly_white", "plotly_dark", "ggplot2"], index=0)

        if st.form_submit_button("Save Settings", type="primary"):
            settings.data_dir = new_data_dir
            settings.db_name = new_db_name
            settings.filter_settings.enabled_by_default = new_enabled
            settings.filter_settings.default_filter_type = new_filter_type
            settings.filter_settings.cfc_class = new_cfc
            settings.filter_settings.lowpass_cutoff_freq = new_cutoff

            settings.save()
            st.success("Settings saved successfully!")
