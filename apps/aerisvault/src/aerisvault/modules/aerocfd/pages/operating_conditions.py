"""aerocfd — Operating Conditions page: free-stream setups for the selected aircraft."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from aerisvault.modules.aerocfd.core.bootstrap import ensure_initialized
from aerisvault.modules.aerocfd.ui.components import aircraft_picker


def render():
    ensure_initialized()
    db = st.session_state["aerocfd.db"]

    st.title("🌬️ Operating Conditions")
    aircraft = aircraft_picker()
    if aircraft is None:
        return

    st.caption(f"Operating conditions for **{aircraft.name}**.")
    list_tab, add_tab = st.tabs(["List", "Add operating condition"])

    with list_tab:
        operating_conditions = db.list_operating_conditions(aircraft.id)
        if not operating_conditions:
            st.info("No operating conditions yet. Add one in the next tab.")
        else:
            table = pd.DataFrame([{
                "Name": oc.name,
                "Velocity [m/s]": oc.velocity_mps,
                "Density [kg/m³]": oc.density_kgpm3,
                "Alpha cases": len(oc.alpha_cases),
            } for oc in operating_conditions])
            st.dataframe(table, use_container_width=True, hide_index=True)

            names = {oc.name: oc for oc in operating_conditions}
            selected = names[st.selectbox("Select to delete:", list(names.keys()))]
            if st.button("🗑️ Delete this operating condition and its alpha cases", type="secondary"):
                db.delete_operating_condition(selected.id)
                st.success(f"Operating condition '{selected.name}' deleted.")
                st.rerun()

    with add_tab:
        with st.form("new_oc"):
            name = st.text_input("Name", placeholder="e.g. SL_50mps")
            description = st.text_area("Description")
            col_v, col_d = st.columns(2)
            velocity = col_v.number_input("Velocity [m/s]", min_value=0.0, value=50.0, step=1.0)
            density = col_d.number_input("Density [kg/m³]", min_value=0.0, value=1.225, step=0.001, format="%.4f")
            if st.form_submit_button("Create operating condition", type="primary"):
                if name:
                    db.create_operating_condition(
                        aircraft_id=aircraft.id, name=name,
                        velocity_mps=velocity, density_kgpm3=density, description=description,
                    )
                    st.success(f"Operating condition '{name}' created.")
                    st.rerun()
                else:
                    st.warning("Please enter a name.")
