"""aerocfd — Analysis page: polars from the stored α cases of the selected operating condition."""
from __future__ import annotations

import numpy as np
import streamlit as st

from aerocfd.viz.plot_utils import (
    cd_alpha_figure, cl_alpha_figure, cm_alpha_figure,
    drag_polar_figure, lift_to_drag_alpha_figure, overlay_alpha_figure,
)

from aerisvault.modules.aerocfd.core.bootstrap import ensure_initialized
from aerisvault.modules.aerocfd.core.mappers import build_dataset
from aerisvault.modules.aerocfd.ui.components import aircraft_picker, operating_condition_picker


def render():
    ensure_initialized()
    db = st.session_state["aerocfd.db"]

    st.title("📈 Analysis")
    aircraft = aircraft_picker()
    if aircraft is None:
        return
    operating_condition = operating_condition_picker(aircraft.id)
    if operating_condition is None:
        return

    alpha_cases = db.list_alpha_cases(operating_condition.id)
    if len(alpha_cases) < 2:
        st.warning("Need at least 2 alpha cases to plot a polar. Add them on the Data Entry page.")
        return

    dataset = build_dataset(aircraft, operating_condition, alpha_cases)
    st.caption(
        f"**{aircraft.name}** · **{operating_condition.name}** · "
        f"{len(alpha_cases)} cases · q∞ = {dataset.dynamic_pressure_pa:.2f} Pa"
    )

    # Pitching moment is referenced to a chosen point (e.g. 20/25/30% MAC); the
    # Cm plots below use this selection.
    references = dataset.reference_points()
    selected_reference = st.selectbox("Moment reference point (Cm)", references) if references else None

    cd_polar = dataset.cd()
    # Runtime echo of gold test #4: negative CD signals a bad input convention.
    if np.any(cd_polar.values < 0):
        st.warning(
            "Some CD values are negative. For a normal draggy body CD should be "
            "positive — check that Fx follows the convention (forward-positive, drag = -X)."
        )

    # Lift, drag, and moment coefficient curves — three tall (1:2) plots side by side.
    lift_col, drag_col, moment_col = st.columns(3)
    lift_col.plotly_chart(cl_alpha_figure(dataset.cl()), width="content")
    drag_col.plotly_chart(cd_alpha_figure(cd_polar), width="content")
    moment_col.plotly_chart(cm_alpha_figure(dataset.cm(reference=selected_reference)), width="content")

    # Efficiency and the aerodynamic (drag) polar — square (1:1) plots.
    efficiency_col, polar_col = st.columns(2)
    efficiency_col.plotly_chart(lift_to_drag_alpha_figure(dataset.lift_to_drag()), width="content")
    polar_col.plotly_chart(drag_polar_figure(dataset.cl(), cd_polar), width="content")

    # --- Per-group decomposition: total + each group's contribution overlaid ---
    groups = dataset.groups()
    if groups:
        st.divider()
        st.subheader("By group")
        st.caption("Total vs each group's contribution (the groups sum to the total).")
        coefficient = st.radio("Coefficient", ["CL", "CD", "Cm"], horizontal=True)
        if coefficient == "Cm":
            curves = [dataset.cm(reference=selected_reference)]
            curves += [dataset.cm(group=g, reference=selected_reference) for g in groups]
        else:
            polar_for = {"CL": dataset.cl, "CD": dataset.cd}[coefficient]
            curves = [polar_for()] + [polar_for(group=g) for g in groups]
        st.plotly_chart(
            overlay_alpha_figure(curves, f"{coefficient} by group", f"{coefficient} [-]"),
            width="content",
        )
