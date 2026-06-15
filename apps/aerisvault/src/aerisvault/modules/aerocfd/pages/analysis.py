"""aerocfd — Analysis page: polars from the stored α cases of the selected operating condition."""
from __future__ import annotations

import numpy as np
import streamlit as st

from aerocfd.viz.plot_utils import (
    cd_alpha_figure, cl_alpha_figure, cm_alpha_figure,
    drag_polar_figure, drag_polar_overlay_figure, lift_to_drag_alpha_figure,
    overlay_alpha_figure,
)

from aerisvault.modules.aerocfd.core.bootstrap import ensure_initialized
from aerisvault.modules.aerocfd.core.mappers import build_dataset
from aerisvault.modules.aerocfd.ui.components import (
    aircraft_picker, operating_condition_picker, variant_picker,
)


def render():
    ensure_initialized()
    db = st.session_state["aerocfd.db"]

    st.title("📈 Analysis")
    aircraft = aircraft_picker()
    if aircraft is None:
        return
    variant = variant_picker(aircraft.id)
    if variant is None:
        return
    operating_condition = operating_condition_picker(variant.id)
    if operating_condition is None:
        return

    alpha_cases = db.list_alpha_cases(operating_condition.id)
    if len(alpha_cases) < 2:
        st.warning("Need at least 2 alpha cases to plot a polar. Add them on the Data Entry page.")
        return

    dataset = build_dataset(aircraft, operating_condition, alpha_cases)
    st.caption(
        f"**{aircraft.name}** · **{variant.name}** · **{operating_condition.name}** · "
        f"{len(alpha_cases)} cases · q∞ = {dataset.dynamic_pressure_pa:.2f} Pa"
    )

    # Pitching moment is referenced to a chosen point (e.g. 20/25/30% MAC). The
    # Cm plots use either the selected point or all of them overlaid.
    references = dataset.reference_points()
    selected_reference = None
    show_all_references = False
    if references:
        col_ref, col_all = st.columns([2, 1])
        show_all_references = col_all.toggle("Show all reference points", value=False)
        selected_reference = col_ref.selectbox(
            "Moment reference point (Cm)", references, disabled=show_all_references,
        )

    cd_polar = dataset.cd()
    # Runtime echo of gold test #4: negative CD signals a bad input convention.
    if np.any(cd_polar.values < 0):
        st.warning(
            "Some CD values are negative. For a normal draggy body CD should be "
            "positive — check that Fx follows the convention (forward-positive, drag = -X)."
        )

    def whole_aircraft_cm_figure():
        """Cm figure for the whole aircraft: all references overlaid, or the one selected."""
        if references and show_all_references:
            curves = [dataset.cm(reference=ref) for ref in references]
            return overlay_alpha_figure(
                curves, "Pitching-moment coefficient vs α — all reference points", "Cm [-]",
            )
        return cm_alpha_figure(dataset.cm(reference=selected_reference))

    # ---- Whole aircraft: CL/CD/Cm (tall) then L/D and drag polar (square) ----
    st.subheader("Whole aircraft")
    lift_col, drag_col, moment_col = st.columns(3)
    lift_col.plotly_chart(cl_alpha_figure(dataset.cl()), width="content")
    drag_col.plotly_chart(cd_alpha_figure(cd_polar), width="content")
    moment_col.plotly_chart(whole_aircraft_cm_figure(), width="content")

    efficiency_col, polar_col = st.columns(2)
    efficiency_col.plotly_chart(lift_to_drag_alpha_figure(dataset.lift_to_drag()), width="content")
    polar_col.plotly_chart(drag_polar_figure(dataset.cl(), cd_polar), width="content")

    # ---- By group: the same figures, each overlaying total + every group ----
    groups = dataset.groups()
    if groups:
        st.divider()
        st.subheader("By group")
        cm_label = f" @ {selected_reference}" if selected_reference else ""
        st.caption(f"Total plus each group (groups sum to the total). Cm at{cm_label or ' the single reference'}.")

        cl_curves = [dataset.cl()] + [dataset.cl(group=g) for g in groups]
        cd_curves = [dataset.cd()] + [dataset.cd(group=g) for g in groups]
        cm_curves = [dataset.cm(reference=selected_reference)]
        cm_curves += [dataset.cm(group=g, reference=selected_reference) for g in groups]

        g_lift, g_drag, g_moment = st.columns(3)
        g_lift.plotly_chart(overlay_alpha_figure(cl_curves, "CL by group", "CL [-]"), width="content")
        g_drag.plotly_chart(overlay_alpha_figure(cd_curves, "CD by group", "CD [-]"), width="content")
        g_moment.plotly_chart(
            overlay_alpha_figure(cm_curves, f"Cm by group{cm_label}", "Cm [-]"), width="content",
        )

        ld_curves = [dataset.lift_to_drag()] + [dataset.lift_to_drag(group=g) for g in groups]
        polar_series = [("Total", dataset.cl(), cd_polar)]
        polar_series += [(g, dataset.cl(group=g), dataset.cd(group=g)) for g in groups]

        g_eff, g_polar = st.columns(2)
        g_eff.plotly_chart(
            overlay_alpha_figure(ld_curves, "L/D by group", "L/D [-]", square=True), width="content",
        )
        g_polar.plotly_chart(drag_polar_overlay_figure(polar_series), width="content")
