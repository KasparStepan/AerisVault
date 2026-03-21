"""Visualization utilities for LS-DYNA post-processing results.

Provides both **Matplotlib** (for local scripts, PDFs, Jupyter) and
**Plotly** (for web rendering in AerisVault UI) plotting functions.

All functions accept a list of ``Curve`` objects and produce figures
without any side effects on the input data.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from dynaprocessing.models.curve import Curve

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: build a display label for a curve
# ---------------------------------------------------------------------------
def _curve_label(curve: Curve) -> str:
    """Build a human-readable legend label from a Curve."""
    lbl = curve.name
    if curve.filter_history:
        lbl += f" ({', '.join(curve.filter_history)})"
    return lbl


def _infer_ylabel(curves: List[Curve]) -> str:
    """Infer a combined Y-axis label from a list of curves."""
    seen: List[str] = []
    for c in curves:
        unit = c.units or "-"
        entry = f"{c.name} [{unit}]"
        if entry not in seen:
            seen.append(entry)
    return ", ".join(seen)


# ===================================================================
# Matplotlib backend
# ===================================================================

def plot_curves(
    curves: List[Curve],
    *,
    title: str = "LS-DYNA Simulation Results",
    xlabel: str = "Time [s]",
    ylabel: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
    grid: bool = True,
    grid_minor: bool = False,
    show: bool = True,
    save_path: Optional[str] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Plot one or more Curves on a single Matplotlib axis.

    Args:
        curves: List of Curve objects to plot.
        title: Figure title.
        xlabel: X-axis label.
        ylabel: Y-axis label (auto-inferred from units if None).
        figsize: Figure dimensions in inches.
        grid: Show major gridlines.
        grid_minor: Show minor gridlines.
        show: Call ``plt.show()`` at the end.
        save_path: Optional path to save the figure (PNG, PDF, SVG, …).

    Returns:
        ``(fig, ax)`` tuple for further customisation.
    """
    fig, ax = plt.subplots(figsize=figsize)

    for curve in curves:
        ax.plot(curve.time, curve.values, label=_curve_label(curve))

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel or _infer_ylabel(curves))

    if grid:
        ax.grid(True, which="major", linestyle="-", alpha=0.8)
    if grid_minor:
        ax.minorticks_on()
        ax.grid(True, which="minor", linestyle=":", alpha=0.5)

    ax.legend(loc="best")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
        logger.info("Plot saved to: %s", save_path)

    if show:
        plt.show()

    return fig, ax


def export_pdf(
    curves: List[Curve],
    output_path: str | Path,
    *,
    combine: bool = False,
    title: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
) -> Path:
    """Export curves to a paginated PDF report.

    Args:
        curves: The curves to render.
        output_path: Destination PDF path.
        combine: If True, overlay all curves on a single page.
            If False, one page per curve.
        title: Optional overall title (used when ``combine=True``).
        figsize: Figure dimensions in inches.

    Returns:
        Resolved Path to the written PDF.
    """
    output_path = Path(output_path).resolve()

    with PdfPages(output_path) as pdf:
        if combine:
            fig, ax = plt.subplots(figsize=figsize)
            for curve in curves:
                ax.plot(curve.time, curve.values, label=_curve_label(curve))
            ax.set_title(title or "Combined Variables over Time")
            ax.set_xlabel("Time [s]")
            ax.set_ylabel(_infer_ylabel(curves))
            ax.grid(True, which="major", linestyle="-", alpha=0.8)
            ax.legend(loc="best")
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)
        else:
            for curve in curves:
                fig, ax = plt.subplots(figsize=figsize)
                ax.plot(curve.time, curve.values, label=_curve_label(curve))
                ax.set_title(f"{curve.name} over Time")
                ax.set_xlabel("Time [s]")
                unit = curve.units or "-"
                ax.set_ylabel(f"{curve.name} [{unit}]")
                ax.grid(True, which="major", linestyle="-", alpha=0.8)
                ax.legend(loc="best")
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close(fig)

    logger.info("PDF report exported to %s", output_path)
    return output_path


# ===================================================================
# Plotly backend (for AerisVault UI / web rendering)
# ===================================================================

def plot_curves_plotly(
    curves: List[Curve],
    *,
    title: str = "LS-DYNA Simulation Results",
    xlabel: str = "Time [s]",
    ylabel: Optional[str] = None,
    science_style: bool = False,
    title_font_size: int = 18,
    axis_font_size: int = 16,
    font_family: str = "Inter, sans-serif",
) -> "plotly.graph_objects.Figure":
    """Create an interactive Plotly figure from Curve objects.

    Args:
        curves: List of Curve objects to plot.
        title: Figure title (centered above the plot).
        xlabel: X-axis label.
        ylabel: Y-axis label (auto-inferred if None).
        science_style: Publication-ready style (black axes, ticks on
            all sides).
        title_font_size: Font size for the figure title.
        axis_font_size: Font size for axis labels (X and Y).
        font_family: CSS font-family string for all text elements.

    Returns:
        A Plotly ``Figure`` object ready for ``st.plotly_chart()``.
    """
    import plotly.graph_objects as go

    fig = go.Figure()

    for curve in curves:
        fig.add_trace(
            go.Scatter(
                x=curve.time,
                y=curve.values,
                mode="lines",
                name=_curve_label(curve),
            )
        )

    resolved_ylabel = ylabel or _infer_ylabel(curves)

    if science_style:
        _apply_science_layout(
            fig, title, xlabel, resolved_ylabel,
            title_font_size=title_font_size,
            axis_font_size=axis_font_size,
            font_family=font_family,
        )
    else:
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=title_font_size, family=font_family),
                x=0.5,
                xanchor="center",
            ),
            xaxis_title=xlabel,
            yaxis_title=resolved_ylabel,
            template="plotly_white",
            font=dict(family=font_family),
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
            xaxis=dict(
                showgrid=True, gridwidth=1, gridcolor="LightGray",
                title_font=dict(size=axis_font_size, family=font_family),
            ),
            yaxis=dict(
                showgrid=True, gridwidth=1, gridcolor="LightGray",
                title_font=dict(size=axis_font_size, family=font_family),
            ),
        )

    return fig


def _apply_science_layout(
    fig: "plotly.graph_objects.Figure",
    title: str,
    xlabel: str,
    ylabel: str,
    *,
    title_font_size: int = 18,
    axis_font_size: int = 16,
    font_family: str = "Times New Roman, Times, serif",
) -> None:
    """Apply a publication-ready layout suitable for scientific papers.

    Style: chosen font, black axes with ticks on all four sides,
    thin grid lines, white background, centered title.
    """
    AXIS_COLOR = "black"
    GRID_COLOR = "rgba(0, 0, 0, 0.15)"

    axis_common = dict(
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID_COLOR,
        linecolor=AXIS_COLOR,
        linewidth=1.5,
        ticks="inside",
        tickwidth=1.5,
        tickcolor=AXIS_COLOR,
        ticklen=6,
        mirror="allticks",
        title_font=dict(size=axis_font_size, family=font_family, color=AXIS_COLOR),
        tickfont=dict(size=13, family=font_family, color=AXIS_COLOR),
        zeroline=False,
    )

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=title_font_size, family=font_family, color=AXIS_COLOR),
            x=0.5,
            xanchor="center",
        ),
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        template="plotly_white",
        font=dict(family=font_family, size=13, color=AXIS_COLOR),
        legend=dict(
            yanchor="top", y=0.99, xanchor="right", x=0.99,
            font=dict(size=12, family=font_family, color=AXIS_COLOR),
            bgcolor="white",
            bordercolor=AXIS_COLOR,
            borderwidth=1,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=50, b=60, l=70, r=30),
        xaxis=axis_common,
        yaxis=axis_common,
    )
