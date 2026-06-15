"""Plotly figure helpers — one function per figure used by the UI.

The library returns Figure objects; the UI passes them to st.plotly_chart with
width="stretch" so they fill the column (and grow with the monitor). The figures
therefore set a fixed *height* only — taller for the coefficient-vs-α curves,
shorter for the L/D curve and the drag polar — and let the width be responsive.
The legend is a horizontal strip below the plot so multi-curve figures use the
full width for the chart rather than squeezing it next to a side legend.
"""
from __future__ import annotations

import plotly.graph_objects as go

from aerocfd.models.polar import Polar

# Fixed heights (px). Width is responsive (set by Streamlit's width="stretch").
COEFFICIENT_HEIGHT_PX = 600   # CL, CD, Cm vs α (and their group/overlay versions)
WIDE_HEIGHT_PX = 460          # L/D vs α and the drag polar

# Legend below the plot, horizontal — keeps the chart full-width.
_LEGEND_BELOW = dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
_MARGIN = dict(l=60, r=20, t=50, b=80)


def _line_figure(x, y, name, title, x_label, y_label, height_px) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=name))
    fig.update_layout(
        title=title, xaxis_title=x_label, yaxis_title=y_label,
        height=height_px, autosize=True, legend=_LEGEND_BELOW, margin=_MARGIN,
    )
    return fig


def _coefficient_alpha_figure(polar: Polar, y_label: str, title: str) -> go.Figure:
    return _line_figure(polar.alpha_deg, polar.values, polar.name, title, "α [deg]", y_label,
                        COEFFICIENT_HEIGHT_PX)


def cl_alpha_figure(cl_polar: Polar) -> go.Figure:
    return _coefficient_alpha_figure(cl_polar, "CL [-]", "Lift coefficient vs α")


def cd_alpha_figure(cd_polar: Polar) -> go.Figure:
    return _coefficient_alpha_figure(cd_polar, "CD [-]", "Drag coefficient vs α")


def cm_alpha_figure(cm_polar: Polar) -> go.Figure:
    # Surface the moment reference point in the title when the polar carries it
    # (e.g. name "Cm @25% MAC"), so the figure is self-explanatory.
    reference = ""
    if "@" in cm_polar.name:
        reference = " @ " + cm_polar.name.split("@", 1)[1].strip()
    return _coefficient_alpha_figure(cm_polar, "Cm [-]", f"Pitching-moment coefficient vs α{reference}")


def lift_to_drag_alpha_figure(ld_polar: Polar) -> go.Figure:
    return _line_figure(ld_polar.alpha_deg, ld_polar.values, ld_polar.name,
                        "Lift-to-drag ratio vs α", "α [deg]", "L/D [-]", WIDE_HEIGHT_PX)


def drag_polar_figure(cl_polar: Polar, cd_polar: Polar) -> go.Figure:
    """Drag polar: CL on Y, CD on X."""
    return _line_figure(cd_polar.values, cl_polar.values, "CL–CD",
                        "Drag polar (CL vs CD)", "CD [-]", "CL [-]", WIDE_HEIGHT_PX)


def overlay_alpha_figure(
    polars: list[Polar], title: str, y_label: str, wide: bool = False
) -> go.Figure:
    """Overlay several α-indexed polars on one figure.

    Used for group decomposition and comparison (total + per-group, or A vs B).
    Each polar's name is its legend entry. Coefficient height by default; the
    shorter `wide` height for L/D so it matches its single-curve counterpart."""
    fig = go.Figure()
    for polar in polars:
        fig.add_trace(go.Scatter(
            x=polar.alpha_deg, y=polar.values, mode="lines+markers", name=polar.name,
        ))
    fig.update_layout(
        title=title, xaxis_title="α [deg]", yaxis_title=y_label,
        height=WIDE_HEIGHT_PX if wide else COEFFICIENT_HEIGHT_PX,
        autosize=True, legend=_LEGEND_BELOW, margin=_MARGIN,
    )
    return fig


def drag_polar_overlay_figure(series: list[tuple[str, Polar, Polar]]) -> go.Figure:
    """Overlay several drag polars (CL vs CD) on one figure.

    `series` is a list of (label, cl_polar, cd_polar) — e.g. the total and each
    group, or A vs B — so their drag polars can be compared on one chart."""
    fig = go.Figure()
    for label, cl_polar, cd_polar in series:
        fig.add_trace(go.Scatter(
            x=cd_polar.values, y=cl_polar.values, mode="lines+markers", name=label,
        ))
    fig.update_layout(
        title="Drag polar (CL vs CD)", xaxis_title="CD [-]", yaxis_title="CL [-]",
        height=WIDE_HEIGHT_PX, autosize=True, legend=_LEGEND_BELOW, margin=_MARGIN,
    )
    return fig
