"""aerocfd — Comparison page: overlay two selections (aircraft / variant / OC)."""
from __future__ import annotations

import numpy as np
import streamlit as st

from aerocfd.analysis.comparison import compare_polars
from aerocfd.models.polar import Polar
from aerocfd.viz.plot_utils import drag_polar_overlay_figure, overlay_alpha_figure

from aerisvault.modules.aerocfd.core.bootstrap import ensure_initialized
from aerisvault.modules.aerocfd.core.csv_export import comparison_dataframe, dataframe_to_csv_bytes
from aerisvault.modules.aerocfd.core.mappers import build_dataset


def _select_dataset(db, side: str):
    """Inline aircraft → variant → OC selection with side-unique widget keys.

    Returns (label, dataset), or None if the selection isn't plottable yet.
    """
    aircraft_list = db.list_aircraft()
    if not aircraft_list:
        st.info("No aircraft yet.")
        return None
    aircraft = st.selectbox("Aircraft", aircraft_list, format_func=lambda a: a.name, key=f"cmp_{side}_ac")

    variants = db.list_variants(aircraft.id)
    variant = st.selectbox("Variant", variants, format_func=lambda v: v.name, key=f"cmp_{side}_var")

    operating_conditions = db.list_operating_conditions(variant.id)
    if not operating_conditions:
        st.info("No operating conditions for this variant.")
        return None
    oc = st.selectbox("Operating condition", operating_conditions, format_func=lambda o: o.name, key=f"cmp_{side}_oc")

    cases = db.list_alpha_cases(oc.id)
    if len(cases) < 2:
        st.warning("Need at least 2 α cases to plot.")
        return None

    label = f"{aircraft.name} / {variant.name} / {oc.name}"
    return label, build_dataset(aircraft, oc, cases)


def _relabel(polar: Polar, name: str) -> Polar:
    """Copy a polar with a new name, so overlays show which selection it is."""
    return Polar(polar.alpha_deg, polar.values, name=name, units=polar.units)


def render():
    ensure_initialized()
    db = st.session_state["aerocfd.db"]

    st.title("⚖️ Comparison")
    st.caption("Overlay two selections — pick an aircraft, variant, and operating condition for each (A and B).")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("A")
        selection_a = _select_dataset(db, "a")
    with col_b:
        st.subheader("B")
        selection_b = _select_dataset(db, "b")
    if selection_a is None or selection_b is None:
        return
    label_a, dataset_a = selection_a
    label_b, dataset_b = selection_b

    st.divider()
    common_refs = [r for r in dataset_a.reference_points() if r in dataset_b.reference_points()]
    selected_ref = st.selectbox("Moment reference point (Cm)", common_refs) if common_refs else None

    # ---- Overlaid polars: CL/CD/Cm (tall), L/D and drag polar (square) ----
    lift_col, drag_col, moment_col = st.columns(3)
    lift_col.plotly_chart(
        overlay_alpha_figure([_relabel(dataset_a.cl(), label_a), _relabel(dataset_b.cl(), label_b)],
                             "CL", "CL [-]"), width="stretch")
    drag_col.plotly_chart(
        overlay_alpha_figure([_relabel(dataset_a.cd(), label_a), _relabel(dataset_b.cd(), label_b)],
                             "CD", "CD [-]"), width="stretch")
    cm_title = "Cm" + (f" @ {selected_ref}" if selected_ref else "")
    moment_col.plotly_chart(
        overlay_alpha_figure([_relabel(dataset_a.cm(reference=selected_ref), label_a),
                              _relabel(dataset_b.cm(reference=selected_ref), label_b)],
                             cm_title, "Cm [-]"), width="stretch")

    eff_col, polar_col = st.columns(2)
    eff_col.plotly_chart(
        overlay_alpha_figure([_relabel(dataset_a.lift_to_drag(), label_a),
                              _relabel(dataset_b.lift_to_drag(), label_b)],
                             "L/D", "L/D [-]", wide=True), width="stretch")
    polar_col.plotly_chart(
        drag_polar_overlay_figure([(label_a, dataset_a.cl(), dataset_a.cd()),
                                   (label_b, dataset_b.cl(), dataset_b.cd())]), width="stretch")

    # ---- Delta table (B − A) at common α + CSV export ----
    st.divider()
    st.subheader("Delta table (B − A) at common α")
    common_alpha = np.array(
        sorted(set(dataset_a.alpha_deg.tolist()) & set(dataset_b.alpha_deg.tolist())), dtype=float,
    )
    if common_alpha.size == 0:
        st.info("The two selections share no common α values, so there is nothing to tabulate.")
        return

    results = {
        "CL": compare_polars(dataset_a.cl(), dataset_b.cl(), common_alpha),
        "CD": compare_polars(dataset_a.cd(), dataset_b.cd(), common_alpha),
        "L/D": compare_polars(dataset_a.lift_to_drag(), dataset_b.lift_to_drag(), common_alpha),
    }
    if selected_ref:
        results[f"Cm@{selected_ref}"] = compare_polars(
            dataset_a.cm(reference=selected_ref), dataset_b.cm(reference=selected_ref), common_alpha,
        )

    table = comparison_dataframe(label_a, label_b, results)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download comparison CSV", dataframe_to_csv_bytes(table),
        file_name="aerocfd_comparison.csv", mime="text/csv",
    )
