"""Plotly figure helpers — one function per figure used by the UI.

The library returns Figure objects; the UI passes them straight to
st.plotly_chart. UI never builds plots itself.
"""
from __future__ import annotations

import plotly.graph_objects as go

from aerocfd.models.polar import Polar


def _alpha_y_figure(polar: Polar, y_label: str, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=polar.alpha_deg, y=polar.values, mode="lines+markers", name=polar.name,
    ))
    fig.update_layout(
        title=title,
        xaxis_title="α [deg]",
        yaxis_title=y_label,
    )
    return fig


def cl_alpha_figure(cl_polar: Polar) -> go.Figure:
    return _alpha_y_figure(cl_polar, "CL [-]", "Lift coefficient vs α")


def cd_alpha_figure(cd_polar: Polar) -> go.Figure:
    return _alpha_y_figure(cd_polar, "CD [-]", "Drag coefficient vs α")


def lift_to_drag_alpha_figure(ld_polar: Polar) -> go.Figure:
    return _alpha_y_figure(ld_polar, "L/D [-]", "Lift-to-drag ratio vs α")


def cm_alpha_figure(cm_polar: Polar) -> go.Figure:
    return _alpha_y_figure(cm_polar, "Cm [-]", "Pitching-moment coefficient vs α")


def drag_polar_figure(cl_polar: Polar, cd_polar: Polar) -> go.Figure:
    """Drag polar: CL on Y, CD on X."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cd_polar.values, y=cl_polar.values, mode="lines+markers", name="CL–CD",
    ))
    fig.update_layout(
        title="Drag polar (CL vs CD)",
        xaxis_title="CD [-]",
        yaxis_title="CL [-]",
    )
    return fig
