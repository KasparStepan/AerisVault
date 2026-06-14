"""aerocfd — Aircraft page: create, edit, and delete aircraft and their reference values."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from aerisvault.modules.aerocfd.core.bootstrap import ensure_initialized


def render():
    ensure_initialized()
    db = st.session_state["aerocfd.db"]

    st.title("✈️ Aircraft")
    registry_tab, add_tab = st.tabs(["Registry", "Add aircraft"])

    # ---- Registry: browse, edit reference values, delete ----
    with registry_tab:
        aircraft = db.list_aircraft()
        if not aircraft:
            st.info("No aircraft yet. Add one in the 'Add aircraft' tab.")
        else:
            table = pd.DataFrame([{
                "Name": a.name,
                "S_ref [m²]": a.s_ref_m2,
                "c_ref [m]": a.c_ref_m,
                "b_ref [m]": a.b_ref_m,
                "Operating conditions": len(a.operating_conditions),
            } for a in aircraft])
            st.dataframe(table, use_container_width=True, hide_index=True)

            names = {a.name: a for a in aircraft}
            selected = names[st.selectbox("Select aircraft to edit or delete:", list(names.keys()))]

            with st.expander("✏️ Edit reference values"):
                # Reference values are load-bearing: every polar for this aircraft is
                # normalized by them. Warn rather than block (single-user posture, §8.6).
                st.warning(
                    "Editing reference values changes every polar already computed for "
                    f"**{selected.name}**. Recompute, or create a new aircraft to compare."
                )
                with st.form(f"edit_aircraft_{selected.id}"):
                    new_name = st.text_input("Name", value=selected.name)
                    new_desc = st.text_area("Description", value=selected.description or "")
                    col_s, col_c, col_b = st.columns(3)
                    new_s = col_s.number_input("S_ref [m²]", value=float(selected.s_ref_m2), min_value=0.0, format="%.4f")
                    new_c = col_c.number_input("c_ref [m]", value=float(selected.c_ref_m), min_value=0.0, format="%.4f")
                    new_b = col_b.number_input("b_ref [m]", value=float(selected.b_ref_m), min_value=0.0, format="%.4f")
                    if st.form_submit_button("Save changes", type="primary"):
                        db.update_aircraft(
                            selected.id, name=new_name, description=new_desc,
                            s_ref_m2=new_s, c_ref_m=new_c, b_ref_m=new_b,
                        )
                        st.success("Aircraft updated.")
                        st.rerun()

            # ---- Parts & groups for the selected aircraft ----
            st.divider()
            st.subheader("Parts & groups")
            st.caption("Define the aircraft's parts and assign each to a group (e.g. Wing, Fuselage, Tail). Per-part loads are entered later on the Data Entry page; totals are summed per group.")
            parts = db.list_parts(selected.id)
            if parts:
                st.dataframe(
                    pd.DataFrame([{"Part": p.name, "Group": p.group_name} for p in parts]),
                    use_container_width=True, hide_index=True,
                )
                part_names = {p.name: p for p in parts}
                to_delete = st.selectbox("Delete a part:", ["—"] + list(part_names.keys()))
                if to_delete != "—" and st.button("Delete part", key=f"del_part_{selected.id}"):
                    db.delete_part(part_names[to_delete].id)
                    st.rerun()
            else:
                st.info("No parts yet. Add the aircraft's parts below.")

            with st.form(f"add_part_{selected.id}"):
                col_name, col_group = st.columns(2)
                part_name = col_name.text_input("Part name", placeholder="e.g. wing, slot, fuselage")
                group_name = col_group.text_input("Group", value="Wing", help="e.g. Wing, Fuselage, Tail")
                if st.form_submit_button("Add part"):
                    if part_name and group_name:
                        db.add_part(selected.id, part_name.strip(), group_name.strip())
                        st.rerun()
                    else:
                        st.warning("Enter both a part name and a group.")

            st.divider()
            st.write("**Danger zone:**")
            if st.button("🗑️ Delete this aircraft and all its operating conditions", type="secondary"):
                db.delete_aircraft(selected.id)
                st.success(f"Aircraft '{selected.name}' deleted.")
                st.rerun()

    # ---- Add a new aircraft ----
    with add_tab:
        with st.form("new_aircraft"):
            name = st.text_input("Name", placeholder="e.g. Glider-X")
            description = st.text_area("Description")
            col_s, col_c, col_b = st.columns(3)
            s_ref = col_s.number_input("S_ref [m²]", min_value=0.0, value=10.0, format="%.4f")
            c_ref = col_c.number_input("c_ref [m]", min_value=0.0, value=1.5, format="%.4f")
            b_ref = col_b.number_input("b_ref [m]", min_value=0.0, value=8.0, format="%.4f")
            if st.form_submit_button("Create aircraft", type="primary"):
                if name:
                    db.create_aircraft(
                        name=name, s_ref_m2=s_ref, c_ref_m=c_ref, b_ref_m=b_ref,
                        description=description,
                    )
                    st.success(f"Aircraft '{name}' created.")
                    st.rerun()
                else:
                    st.warning("Please enter a name.")
