"""
AerisVault UI - Reusable Components
Streamlit widget utilities for consistent look and feel.
"""

import streamlit as st
from typing import List, Callable, Optional


def info_card(title: str, value: str, icon: str = "ℹ️"):
    """Display a small metric-like card with an icon."""
    st.markdown(
        f"""
        <div style="padding: 15px; border-radius: 10px; border: 1px solid #ddd; background-color: #f8f9fa;">
            <span style="font-size: 20px;">{icon}</span>
            <span style="color: #666; font-size: 14px; margin-left: 5px;">{title}</span>
            <div style="font-size: 24px; font-weight: bold; margin-top: 5px;">{value}</div>
        </div>
        """, 
        unsafe_allow_html=True
    )


FONT_OPTIONS = [
    "Inter, sans-serif",
    "Roboto, sans-serif",
    "Open Sans, sans-serif",
    "Helvetica, Arial, sans-serif",
    "Times New Roman, Times, serif",
    "Georgia, serif",
    "Courier New, monospace",
]

# Short display names for the selectbox
_FONT_DISPLAY = {
    "Inter, sans-serif": "Inter",
    "Roboto, sans-serif": "Roboto",
    "Open Sans, sans-serif": "Open Sans",
    "Helvetica, Arial, sans-serif": "Helvetica",
    "Times New Roman, Times, serif": "Times New Roman",
    "Georgia, serif": "Georgia",
    "Courier New, monospace": "Courier New",
}


def sidebar_plot_style() -> dict:
    """Display figure style controls at the bottom of the sidebar.

    Returns:
        Dict with keys: science_style, title_font_size, axis_font_size,
        font_family.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎨 Figure Settings")

    science = st.sidebar.toggle(
        "Science style (publication-ready)",
        value=False,
        help="Black axes with ticks on all sides — suitable for papers.",
    )

    display_names = [_FONT_DISPLAY[f] for f in FONT_OPTIONS]
    selected_display = st.sidebar.selectbox(
        "Font",
        display_names,
        index=0,
    )
    font_family = FONT_OPTIONS[display_names.index(selected_display)]

    title_size = st.sidebar.slider("Title font size", 10, 32, 18)
    axis_size = st.sidebar.slider("Axis label font size", 10, 32, 16)

    return {
        "science_style": science,
        "title_font_size": title_size,
        "axis_font_size": axis_size,
        "font_family": font_family,
    }


def sidebar_filter_settings():
    """Display filter settings in the sidebar and return them as a dict."""
    settings = st.session_state["fsi.settings"].filter_settings
    
    st.sidebar.subheader("🔧 Filter Settings")
    
    enabled = st.sidebar.toggle(
        "Apply Filtering", 
        value=settings.enabled_by_default
    )
    
    if not enabled:
        return {"enabled": False}
        
    filter_type = st.sidebar.selectbox(
        "Filter Type",
        ["cfc", "butterworth", "moving_average", "savgol"],
        index=["cfc", "butterworth", "moving_average", "savgol"].index(
            settings.default_filter_type
        )
    )
    
    params = {"enabled": True, "type": filter_type}
    
    if filter_type == "cfc":
        params["cfc"] = st.sidebar.select_slider(
            "CFC Class",
            options=[60, 180, 600, 1000],
            value=settings.cfc_class
        )
    elif filter_type == "butterworth":
        params["cutoff"] = st.sidebar.number_input(
            "Cutoff (Hz)", value=settings.lowpass_cutoff_freq
        )
    elif filter_type == "moving_average":
        params["window"] = st.sidebar.number_input(
            "Window Size", value=settings.moving_avg_window, min_value=1
        )
    elif filter_type == "savgol":
        params["window"] = st.sidebar.number_input(
            "Window Length", value=settings.savgol_window_length, min_value=3, step=2
        )
        params["order"] = st.sidebar.number_input(
            "Poly Order", value=settings.savgol_polyorder, min_value=1
        )
        
    return params


def simulation_selector(label: str = "Select Simulation", key: str = "sim_selector"):
    """Standard simulation dropdown menu."""
    db = st.session_state["fsi.db"]
    sims = db.list_simulations()
    
    if not sims:
        st.warning("No simulations found in database.")
        return None
        
    sim_names = [s.name for s in sims]
    selected_name = st.selectbox(label, sim_names, key=key)
    
    return next(s for s in sims if s.name == selected_name)
