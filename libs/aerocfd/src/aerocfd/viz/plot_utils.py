"""Plotly figure helpers — one function per figure used by the UI.

The library returns Figure objects; the UI passes them straight to
st.plotly_chart. UI never builds plots itself.

Aspect ratio: aerodynamic polars are drawn tall — height is twice the width
(1:2 width:height). The figures carry explicit pixel dimensions so this ratio
is honored regardless of the container; the page renders them at intrinsic
size rather than stretching to the column width.
"""
from __future__ import annotations

import plotly.graph_objects as go

from aerocfd.models.polar import Polar

# Tall 1:2 (width:height) aerodynamic convention. Adjust both to resize while
# keeping the ratio; FIGURE_HEIGHT_PX must stay 2 × FIGURE_WIDTH_PX.
FIGURE_WIDTH_PX = 450
FIGURE_HEIGHT_PX = 2 * FIGURE_WIDTH_PX


def _apply_aero_layout(fig: go.Figure, title: str, x_label: str, y_label: str) -> go.Figure:
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        width=FIGURE_WIDTH_PX,
        height=FIGURE_HEIGHT_PX,
        autosize=False,
    )
    return fig


def _alpha_y_figure(polar: Polar, y_label: str, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=polar.alpha_deg, y=polar.values, mode="lines+markers", name=polar.name,
    ))
    return _apply_aero_layout(fig, title, "α [deg]", y_label)


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
    return _apply_aero_layout(fig, "Drag polar (CL vs CD)", "CD [-]", "CL [-]")
