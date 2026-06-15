"""Plotly figure helpers — one function per figure used by the UI.

The library returns Figure objects; the UI passes them straight to
st.plotly_chart. UI never builds plots itself.

Aspect ratios (figures carry explicit pixel dimensions so the ratio is honored
regardless of the container; the page renders them at intrinsic size):
- The coefficient-vs-α curves (CL, CD, Cm) are drawn tall, 1:2 width:height —
  the aerodynamic convention. They sit three-across (lift, drag, moment).
- The efficiency curve (L/D) and the drag polar (CL–CD) are drawn square, 1:1.
"""
from __future__ import annotations

import plotly.graph_objects as go

from aerocfd.models.polar import Polar

# Tall 1:2 (width:height) for the coefficient-vs-α curves. Adjust to resize;
# TALL_HEIGHT_PX must stay 2 × TALL_WIDTH_PX.
TALL_WIDTH_PX = 360
TALL_HEIGHT_PX = 2 * TALL_WIDTH_PX

# Square 1:1 for the efficiency curve and the drag polar.
SQUARE_SIZE_PX = 520


def _line_figure(x, y, name, title, x_label, y_label, width_px, height_px) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=name))
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        width=width_px,
        height=height_px,
        autosize=False,
    )
    return fig


def _tall_alpha_figure(polar: Polar, y_label: str, title: str) -> go.Figure:
    return _line_figure(
        polar.alpha_deg, polar.values, polar.name, title, "α [deg]", y_label,
        TALL_WIDTH_PX, TALL_HEIGHT_PX,
    )


def cl_alpha_figure(cl_polar: Polar) -> go.Figure:
    return _tall_alpha_figure(cl_polar, "CL [-]", "Lift coefficient vs α")


def cd_alpha_figure(cd_polar: Polar) -> go.Figure:
    return _tall_alpha_figure(cd_polar, "CD [-]", "Drag coefficient vs α")


def cm_alpha_figure(cm_polar: Polar) -> go.Figure:
    # Surface the moment reference point in the title when the polar carries it
    # (e.g. name "Cm @25% MAC"), so the figure is self-explanatory.
    reference = ""
    if "@" in cm_polar.name:
        reference = " @ " + cm_polar.name.split("@", 1)[1].strip()
    return _tall_alpha_figure(cm_polar, "Cm [-]", f"Pitching-moment coefficient vs α{reference}")


def lift_to_drag_alpha_figure(ld_polar: Polar) -> go.Figure:
    """Efficiency curve — drawn square (1:1)."""
    return _line_figure(
        ld_polar.alpha_deg, ld_polar.values, ld_polar.name,
        "Lift-to-drag ratio vs α", "α [deg]", "L/D [-]",
        SQUARE_SIZE_PX, SQUARE_SIZE_PX,
    )


def drag_polar_figure(cl_polar: Polar, cd_polar: Polar) -> go.Figure:
    """Drag polar: CL on Y, CD on X — drawn square (1:1)."""
    return _line_figure(
        cd_polar.values, cl_polar.values, "CL–CD",
        "Drag polar (CL vs CD)", "CD [-]", "CL [-]",
        SQUARE_SIZE_PX, SQUARE_SIZE_PX,
    )


def overlay_alpha_figure(
    polars: list[Polar], title: str, y_label: str, square: bool = False
) -> go.Figure:
    """Overlay several α-indexed polars on one figure.

    Used for group decomposition (total + per-group contributions). Each polar's
    name becomes its legend entry (e.g. 'CL', 'CL (Wing)', 'CL (Fuselage)').
    Tall (1:2) by default; square (1:1) when `square` is True — so a by-group
    figure can match the shape of its whole-aircraft counterpart."""
    fig = go.Figure()
    for polar in polars:
        fig.add_trace(go.Scatter(
            x=polar.alpha_deg, y=polar.values, mode="lines+markers", name=polar.name,
        ))
    width, height = (SQUARE_SIZE_PX, SQUARE_SIZE_PX) if square else (TALL_WIDTH_PX, TALL_HEIGHT_PX)
    fig.update_layout(
        title=title, xaxis_title="α [deg]", yaxis_title=y_label,
        width=width, height=height, autosize=False,
    )
    return fig


def drag_polar_overlay_figure(series: list[tuple[str, Polar, Polar]]) -> go.Figure:
    """Overlay several drag polars (CL vs CD) on one square figure.

    `series` is a list of (label, cl_polar, cd_polar) — e.g. the total and each
    group — so the groups' drag polars can be compared on one chart."""
    fig = go.Figure()
    for label, cl_polar, cd_polar in series:
        fig.add_trace(go.Scatter(
            x=cd_polar.values, y=cl_polar.values, mode="lines+markers", name=label,
        ))
    fig.update_layout(
        title="Drag polar by group", xaxis_title="CD [-]", yaxis_title="CL [-]",
        width=SQUARE_SIZE_PX, height=SQUARE_SIZE_PX, autosize=False,
    )
    return fig
