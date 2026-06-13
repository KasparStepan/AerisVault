"""
AerisVault - Settings
Application settings and theme configuration.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aerisvault.database import SimulationDatabase
from aerisvault.config import get_settings

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings")
st.caption("Configure AerisVault application settings")

# Theme Section
st.subheader("🎨 Appearance")

# Initialize theme in session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

col1, col2 = st.columns([2, 1])
with col1:
    theme = st.radio(
        "Theme Mode",
        ["☀️ Light", "🌙 Dark"],
        horizontal=True,
        index=0 if st.session_state.theme == 'light' else 1
    )
    
    if "Light" in theme:
        st.session_state.theme = 'light'
    else:
        st.session_state.theme = 'dark'

with col2:
    st.info(f"Current: **{st.session_state.theme.title()}** mode")

st.markdown("""
> **Note:** To fully apply theme changes, add the following to your `.streamlit/config.toml`:
> ```toml
> [theme]
> base = "light"  # or "dark"
> ```
""")

st.divider()

# Export Settings
st.subheader("📤 Export Settings")

settings = get_settings()

col1, col2 = st.columns(2)
with col1:
    export_format = st.selectbox(
        "Default Image Format",
        ["PNG", "SVG", "PDF", "HTML"],
        index=0
    )
    
    export_width = st.number_input("Image Width (px)", value=1200, min_value=400, max_value=4000)

with col2:
    export_height = st.number_input("Image Height (px)", value=600, min_value=300, max_value=2000)
    export_scale = st.number_input("Scale Factor", value=2.0, min_value=1.0, max_value=4.0, step=0.5)

st.divider()

# Filter Settings
st.subheader("🔧 Filter Settings")

with st.form("filter_settings_form"):
    enable_filter = st.checkbox(
        "Enable filtering by default",
        value=settings.filter_settings.enabled_by_default
    )
    
    filter_type = st.selectbox(
        "Default filter type",
        ["savgol", "moving_average", "lowpass"],
        index=["savgol", "moving_average", "lowpass"].index(
            settings.filter_settings.default_filter_type
        )
    )
    
    col1, col2 = st.columns(2)
    with col1:
        savgol_window = st.number_input(
            "Savgol window length",
            value=settings.filter_settings.savgol_window_length,
            min_value=5,
            step=2
        )
        savgol_poly = st.number_input(
            "Savgol polynomial order",
            value=settings.filter_settings.savgol_polyorder,
            min_value=1,
            max_value=5
        )
    with col2:
        moving_avg_window = st.number_input(
            "Moving average window",
            value=settings.filter_settings.moving_avg_window,
            min_value=2
        )
        lowpass_cutoff = st.number_input(
            "Lowpass cutoff frequency (Hz)",
            value=settings.filter_settings.lowpass_cutoff_freq,
            min_value=0.1
        )
    
    if st.form_submit_button("💾 Save Filter Settings", type="primary"):
        settings.filter_settings.enabled_by_default = enable_filter
        settings.filter_settings.default_filter_type = filter_type
        settings.filter_settings.savgol_window_length = int(savgol_window)
        settings.filter_settings.savgol_polyorder = int(savgol_poly)
        settings.filter_settings.moving_avg_window = int(moving_avg_window)
        settings.filter_settings.lowpass_cutoff_freq = float(lowpass_cutoff)
        settings.save()
        st.success("✅ Settings saved!")

st.divider()

# Plot Settings
st.subheader("📊 Plot Settings")

with st.form("plot_settings_form"):
    theme_plot = st.selectbox(
        "Plot theme",
        ["plotly_white", "plotly_dark", "plotly", "simple_white"],
        index=["plotly_white", "plotly_dark", "plotly", "simple_white"].index(
            settings.plot_settings.theme
        )
    )
    
    col1, col2 = st.columns(2)
    with col1:
        width = st.number_input("Default width", value=settings.plot_settings.width, min_value=400)
        line_width = st.number_input("Line width", value=settings.plot_settings.line_width, min_value=1)
    with col2:
        height = st.number_input("Default height", value=settings.plot_settings.height, min_value=300)
        font_size = st.number_input("Font size", value=settings.plot_settings.font_size, min_value=8)
    
    show_grid = st.checkbox("Show grid", value=settings.plot_settings.show_grid)
    
    if st.form_submit_button("💾 Save Plot Settings", type="primary"):
        settings.plot_settings.theme = theme_plot
        settings.plot_settings.width = int(width)
        settings.plot_settings.height = int(height)
        settings.plot_settings.line_width = int(line_width)
        settings.plot_settings.font_size = int(font_size)
        settings.plot_settings.show_grid = show_grid
        settings.save()
        st.success("✅ Settings saved!")

st.divider()

# Storage Info
st.subheader("💾 Storage Information")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**Data directory:** `{settings.data_dir}`")
with col2:
    st.write(f"**Max file size:** {settings.max_file_size_mb} MB")