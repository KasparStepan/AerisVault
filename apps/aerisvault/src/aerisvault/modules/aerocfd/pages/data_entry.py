"""aerocfd — Data Entry page: edit the α-case table for the selected operating condition."""
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

    st.title("⌨️ Data Entry — alpha cases")
    aircraft = aircraft_picker()
    if aircraft is None:
        return
    operating_condition = operating_condition_picker(aircraft.id)
    if operating_condition is None:
        return

    st.caption(
        "Body-frame totals exactly as Fluent reports them. Fx is forward-positive, "
        "so a draggy body has Fx < 0; My is raw (the library applies the sign flip)."
    )

    existing = db.list_alpha_cases(operating_condition.id)
    if existing:
        table = pd.DataFrame([{
            "alpha_deg": c.alpha_deg,
            "fx_n": c.fx_n,
            "fz_n": c.fz_n,
            "my_nm": c.my_nm,
            "convergence_status": c.convergence_status,
        } for c in existing])
    else:
        # Starter template for a fresh operating condition.
        table = pd.DataFrame({
            "alpha_deg": [-5.0, 0.0, 5.0, 10.0, 15.0],
            "fx_n":      [-12.0, -10.0, -15.0, -30.0, -55.0],
            "fz_n":      [-300.0, 200.0, 700.0, 1200.0, 1600.0],
            "my_nm":     [-25.0, 0.0, 25.0, 50.0, 75.0],
            "convergence_status": [ConvergenceStatus.UNKNOWN.value] * 5,
        })

    edited = st.data_editor(
        table,
        num_rows="dynamic",
        column_config={
            "alpha_deg": st.column_config.NumberColumn("α [deg]", format="%.2f"),
            "fx_n": st.column_config.NumberColumn("Fx [N]", help="Body x, forward-positive (drag is -X, so Fx<0)", format="%.3f"),
            "fz_n": st.column_config.NumberColumn("Fz [N]", format="%.3f"),
            "my_nm": st.column_config.NumberColumn("My [N·m]", help="Raw Fluent My (sign-flipped in library)", format="%.3f"),
            "convergence_status": st.column_config.SelectboxColumn("Convergence", options=_STATUS_OPTIONS),
        },
        use_container_width=True,
    )

    if st.button("💾 Save alpha cases", type="primary"):
        rows = []
        for _, row in edited.iterrows():
            if pd.isna(row["alpha_deg"]):
                continue
            rows.append({
                "alpha_deg": float(row["alpha_deg"]),
                "fx_n": float(row["fx_n"]),
                "fz_n": float(row["fz_n"]),
                "my_nm": float(row["my_nm"]),
                "convergence_status": row["convergence_status"] or ConvergenceStatus.UNKNOWN.value,
            })
        saved = db.replace_alpha_cases(operating_condition.id, rows)
        st.success(f"Saved {saved} alpha case(s) for '{operating_condition.name}'.")
        st.rerun()
