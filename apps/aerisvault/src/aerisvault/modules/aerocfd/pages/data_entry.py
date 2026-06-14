"""aerocfd — Data Entry page: per-part body-frame loads for one α at a time."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from aerocfd.models.alpha_case import ConvergenceStatus

from aerisvault.modules.aerocfd.core.bootstrap import ensure_initialized
from aerisvault.modules.aerocfd.ui.components import aircraft_picker, operating_condition_picker

_STATUS_OPTIONS = [s.value for s in ConvergenceStatus]


def render():
    ensure_initialized()
    db = st.session_state["aerocfd.db"]

    st.title("⌨️ Data Entry — per-part loads")
    aircraft = aircraft_picker()
    if aircraft is None:
        return
    operating_condition = operating_condition_picker(aircraft.id)
    if operating_condition is None:
        return

    parts = sorted(db.list_parts(aircraft.id), key=lambda p: (p.group_name, p.display_order))
    if not parts:
        st.warning("This aircraft has no parts yet. Define them on the Aircraft page → 'Parts & groups'.")
        return
    reference_points = db.list_reference_points(aircraft.id)

    st.caption(
        "Enter each part's body-frame total at one angle of attack. Fx is "
        "forward-positive (drag is −X, so a draggy part has Fx < 0); My is raw "
        "(the library applies the sign flip). Totals are summed from the parts."
    )

    # --- Pick which α to edit: an existing one, or a new value ---
    existing_cases = db.list_alpha_cases(operating_condition.id)
    existing_alphas = [c.alpha_deg for c in existing_cases]
    if existing_alphas:
        st.write("Saved α: " + "  ".join(f"`{a:g}°`" for a in existing_alphas))

    options = ["➕ New α…"] + [f"{a:g}°" for a in existing_alphas]
    col_pick, col_alpha = st.columns([2, 1])
    chosen = col_pick.selectbox("Angle of attack", options)
    if chosen == "➕ New α…":
        alpha_deg = col_alpha.number_input("New α [deg]", value=0.0, step=1.0, format="%.2f")
        current_case = db.get_alpha_case(operating_condition.id, alpha_deg)
    else:
        alpha_deg = existing_alphas[options.index(chosen) - 1]
        col_alpha.metric("α", f"{alpha_deg:g}°")
        current_case = existing_cases[options.index(chosen) - 1]

    # Pre-fill from the existing case for this α, else zeros. One moment column
    # per reference point (My@<label>).
    loads_by_part = {pl.part_id: pl for pl in (current_case.part_loads if current_case else [])}

    def moment_value(load, label):
        if load is None:
            return 0.0
        return next((m.my_nm for m in load.moments if m.reference_point.label == label), 0.0)

    rows = []
    for part in parts:
        load = loads_by_part.get(part.id)
        row = {
            "Part": part.name,
            "Group": part.group_name,
            "Fx [N]": load.fx_n if load else 0.0,
            "Fz [N]": load.fz_n if load else 0.0,
        }
        for ref in reference_points:
            row[f"My@{ref.label}"] = moment_value(load, ref.label)
        rows.append(row)
    table = pd.DataFrame(rows)

    column_config = {
        "Fx [N]": st.column_config.NumberColumn(format="%.4f"),
        "Fz [N]": st.column_config.NumberColumn(format="%.4f"),
    }
    for ref in reference_points:
        column_config[f"My@{ref.label}"] = st.column_config.NumberColumn(
            f"My@{ref.label} [N·m]", format="%.4f",
        )

    if not reference_points:
        st.info("No moment reference points defined — add them on the Aircraft page to enter Cm data.")

    edited = st.data_editor(
        table,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",  # one row per defined part; positional mapping back to parts
        disabled=["Part", "Group"],
        column_config=column_config,
    )

    status_default = current_case.convergence_status if current_case else ConvergenceStatus.UNKNOWN.value
    convergence = st.selectbox(
        "Convergence", _STATUS_OPTIONS,
        index=_STATUS_OPTIONS.index(status_default) if status_default in _STATUS_OPTIONS else _STATUS_OPTIONS.index("unknown"),
    )

    col_save, col_delete = st.columns([1, 1])
    if col_save.button("💾 Save this α case", type="primary"):
        loads = []
        for part, (_, row) in zip(parts, edited.iterrows()):
            moments = {ref.id: float(row[f"My@{ref.label}"]) for ref in reference_points}
            loads.append({
                "part_id": part.id,
                "fx_n": float(row["Fx [N]"]),
                "fz_n": float(row["Fz [N]"]),
                "moments": moments,
            })
        db.set_alpha_case(operating_condition.id, float(alpha_deg), loads, convergence_status=convergence)
        st.success(f"Saved α = {alpha_deg:g}° ({len(loads)} parts) for '{operating_condition.name}'.")
        st.rerun()

    if current_case and col_delete.button("🗑️ Delete this α case"):
        db.delete_alpha_case(current_case.id)
        st.rerun()
