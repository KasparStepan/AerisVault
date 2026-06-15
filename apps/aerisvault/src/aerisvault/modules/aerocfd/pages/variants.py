"""aerocfd — Variants page: configurations of an aircraft (e.g. VOP settings)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from aerisvault.modules.aerocfd.core.bootstrap import ensure_initialized
from aerisvault.modules.aerocfd.ui.components import aircraft_picker


def _fmt(value) -> str:
    return "—" if value is None else f"{value:g}"


def render():
    ensure_initialized()
    db = st.session_state["aerocfd.db"]

    st.title("🛩️ Variants")
    st.caption(
        "A variant is a configuration of the same physical aircraft (e.g. a VOP "
        "angle or arm). It owns its operating conditions. VOP angle/arm are recorded "
        "for the future trim model and do not change the computed coefficients yet."
    )
    aircraft = aircraft_picker()
    if aircraft is None:
        return

    list_tab, add_tab = st.tabs(["List", "Add variant"])

    with list_tab:
        variants = db.list_variants(aircraft.id)
        st.dataframe(
            pd.DataFrame([{
                "Variant": v.name,
                "VOP angle [deg]": _fmt(v.vop_angle_deg),
                "VOP arm [m]": _fmt(v.vop_arm_m),
                "Operating conditions": len(v.operating_conditions),
            } for v in variants]),
            use_container_width=True, hide_index=True,
        )

        names = {v.name: v for v in variants}
        selected = names[st.selectbox("Edit / delete variant:", list(names.keys()))]
        with st.expander("✏️ Edit variant"):
            with st.form(f"edit_variant_{selected.id}"):
                new_name = st.text_input("Name", value=selected.name)
                new_desc = st.text_area("Description", value=selected.description or "")
                col_a, col_b = st.columns(2)
                new_angle = col_a.number_input(
                    "VOP angle [deg]", value=float(selected.vop_angle_deg or 0.0), format="%.3f",
                )
                new_arm = col_b.number_input(
                    "VOP arm from CG [m]", value=float(selected.vop_arm_m or 0.0), min_value=0.0, format="%.3f",
                )
                if st.form_submit_button("Save changes", type="primary"):
                    db.update_variant(
                        selected.id, name=new_name, description=new_desc,
                        vop_angle_deg=new_angle, vop_arm_m=new_arm,
                    )
                    st.success("Variant updated.")
                    st.rerun()

        # Keep at least one variant so operating conditions always have a parent.
        if len(variants) > 1:
            if st.button("🗑️ Delete this variant and its operating conditions", type="secondary"):
                db.delete_variant(selected.id)
                st.rerun()
        else:
            st.caption("An aircraft keeps at least one variant.")

    with add_tab:
        with st.form("new_variant"):
            name = st.text_input("Name", placeholder="e.g. VOP +2°, arm 4.5 m")
            description = st.text_area("Description")
            col_a, col_b = st.columns(2)
            angle = col_a.number_input("VOP angle [deg]", value=0.0, format="%.3f")
            arm = col_b.number_input("VOP arm from CG [m]", value=0.0, min_value=0.0, format="%.3f")
            if st.form_submit_button("Create variant", type="primary"):
                if name:
                    db.create_variant(aircraft.id, name, description=description,
                                      vop_angle_deg=angle, vop_arm_m=arm)
                    st.success(f"Variant '{name}' created.")
                    st.rerun()
                else:
                    st.warning("Please enter a name.")
