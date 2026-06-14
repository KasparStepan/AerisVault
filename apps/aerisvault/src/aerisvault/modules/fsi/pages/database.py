"""
AerisVault UI - Database Page
Simulation registry: browse, add, edit, delete simulations and manage tags.
"""

import streamlit as st
import pandas as pd
from aerisvault.modules.fsi.core.models import FileType
from aerisvault.modules.fsi.core.bootstrap import ensure_initialized


def render():
    ensure_initialized()
    db = st.session_state["fsi.db"]
    storage = st.session_state["fsi.storage"]

    st.title("🗄️ Simulation Database")

    tabs = st.tabs(["🚀 Registry", "➕ Add Simulation", "🏷️ Tags"])


    # ---------------------------------------------------------------------------
    # Registry Tab — browse, edit, delete simulations
    # ---------------------------------------------------------------------------
    with tabs[0]:
        sims = db.list_simulations()

        if not sims:
            st.info("No simulations yet. Go to 'Add Simulation' to register one.")
        else:
            # Search bar
            search = st.text_input("🔍 Search by name", placeholder="Filter simulations...")
            if search:
                sims = [s for s in sims if search.lower() in s.name.lower()]

            # Summary table
            table_data = []
            for s in sims:
                table_data.append({
                    "Name": s.name,
                    "Type": s.analysis_type.replace("_", " ").title(),
                    "Date": s.created_at.strftime("%Y-%m-%d"),
                    "Files": len(s.files),
                    "V (m/s)": s.velocity if s.velocity else "—",
                    "Area (m²)": s.ref_area if s.ref_area else "—",
                    "Tags": ", ".join([t.name for t in s.tags]) if s.tags else "—",
                })
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

            st.divider()

            # Detail / edit / delete panel for a selected simulation
            selected_name = st.selectbox("Select simulation to view or edit:", [s.name for s in sims])
            selected_sim = next(s for s in sims if s.name == selected_name)

            col_info, col_actions = st.columns([3, 1])

            with col_info:
                st.write(f"### {selected_sim.name}")
                st.write(f"**Type:** {selected_sim.analysis_type.replace('_', ' ').title()}")
                st.write(selected_sim.description or "*No description*")

                files = selected_sim.files
                if files:
                    st.write("**Attached files:**")
                    for f in files:
                        col_f, col_del = st.columns([6, 1])
                        col_f.write(f"- `{f.original_filename}` ({f.storage_format}, {f.file_size_bytes / 1024:.1f} KB)")
                        if col_del.button("🗑️", key=f"del_file_{f.id}", help="Delete this file"):
                            storage.delete_file(f.storage_path)
                            db.delete_file(f.id)
                            st.rerun()

            with col_actions:
                st.metric("Velocity", f"{selected_sim.velocity or '—'} m/s")
                st.metric("Ref Area", f"{selected_sim.ref_area or '—'} m²")

            # Tag management for the selected simulation
            st.divider()
            all_tags = db.list_all_tags()
            col_tags, col_add_tag = st.columns([3, 2])

            with col_tags:
                st.write("**Tags on this simulation:**")
                if selected_sim.tags:
                    for tag in selected_sim.tags:
                        col_t, col_rm = st.columns([5, 1])
                        col_t.markdown(
                            f'<span style="background:{tag.color or "#ccc"};padding:2px 8px;border-radius:4px;color:#fff">'
                            f'{tag.name}</span>',
                            unsafe_allow_html=True,
                        )
                        if col_rm.button("✕", key=f"rm_tag_{selected_sim.id}_{tag.id}"):
                            db.remove_tag_from_simulation(selected_sim.id, tag.name)
                            st.rerun()
                else:
                    st.write("*No tags assigned*")

            with col_add_tag:
                available_tags = [t.name for t in all_tags if t not in selected_sim.tags]
                if available_tags:
                    tag_to_add = st.selectbox("Add tag:", ["— select —"] + available_tags, key="tag_add_select")
                    if st.button("Add tag", key="btn_add_tag") and tag_to_add != "— select —":
                        db.add_tags_to_simulation(selected_sim.id, [tag_to_add])
                        st.rerun()
                else:
                    st.write("*All tags assigned*")

            # Edit and Delete
            st.divider()
            with st.expander("✏️ Edit this simulation"):
                with st.form(f"edit_sim_{selected_sim.id}"):
                    new_name = st.text_input("Name", value=selected_sim.name)
                    new_desc = st.text_area("Description", value=selected_sim.description or "")

                    new_type = st.radio(
                        "Analysis type",
                        options=["infinite_mass", "finite_mass"],
                        index=0 if selected_sim.analysis_type == "infinite_mass" else 1,
                        format_func=lambda x: "Infinite Mass" if x == "infinite_mass" else "Finite Mass",
                        horizontal=True,
                    )

                    col1, col2, col3, col4 = st.columns(4)
                    new_vel = col1.number_input("Velocity (m/s)", value=float(selected_sim.velocity or 0.0), min_value=0.0)
                    new_area = col2.number_input("Ref Area (m²)", value=float(selected_sim.ref_area or 0.0), min_value=0.0)
                    new_density = col3.number_input("Air density (kg/m³)", value=float(selected_sim.air_density), min_value=0.0)
                    new_mass = col4.number_input("Mass (kg)", value=float(selected_sim.mass or 0.0), min_value=0.0)

                    if st.form_submit_button("Save changes", type="primary"):
                        db.update_simulation(
                            selected_sim.id,
                            name=new_name,
                            description=new_desc,
                            analysis_type=new_type,
                            velocity=new_vel if new_vel > 0 else None,
                            ref_area=new_area if new_area > 0 else None,
                            air_density=new_density,
                            mass=new_mass if new_mass > 0 else None,
                        )
                        st.success("Simulation updated.")
                        st.rerun()

                # File management — outside the form so upload works without submit
                st.markdown("**Upload additional files:**")
                new_files = st.file_uploader(
                    "Drop files here",
                    accept_multiple_files=True,
                    key=f"upload_edit_{selected_sim.id}",
                    help="Upload .dat or .csv result files to attach to this simulation.",
                )
                if new_files and st.button("Attach files", key=f"btn_attach_{selected_sim.id}", type="primary"):
                    for f in new_files:
                        content = f.read()
                        path, fmt, size, meta = storage.store_file(
                            content, f.name, FileType.DRAG_RESULT, selected_sim.id
                        )
                        db.create_file(
                            selected_sim.id, f.name, path, FileType.DRAG_RESULT, fmt, size, meta
                        )
                    st.success(f"{len(new_files)} file(s) attached.")
                    st.rerun()

            # Delete button — placed outside expander so it's visible but separate
            st.write("**Danger zone:**")
            if st.button("🗑️ Delete this simulation and all its files", type="secondary"):
                # Delete physical files first
                for f in selected_sim.files:
                    storage.delete_file(f.storage_path)
                # Delete database record (cascades to files)
                db.delete_simulation(selected_sim.id)
                st.success(f"Simulation '{selected_sim.name}' deleted.")
                st.rerun()


    # ---------------------------------------------------------------------------
    # Add Simulation Tab
    # ---------------------------------------------------------------------------
    with tabs[1]:
        st.subheader("Register a New Simulation")

        with st.form("new_sim"):
            name = st.text_input("Name", placeholder="e.g. cross_2m_6ms_run01")
            desc = st.text_area("Description")

            analysis_type = st.radio(
                "Analysis type",
                options=["infinite_mass", "finite_mass"],
                format_func=lambda x: (
                    "Infinite Mass — ICFD wind-tunnel (.dat files with force columns: Fpx, Fpy, Fpz)"
                    if x == "infinite_mass"
                    else "Finite Mass — Drop test (.csv files with kinematic columns: z_acceleration, z_velocity)"
                ),
                help="This tells the app which parser to use when loading results for analysis.",
            )

            col1, col2, col3 = st.columns(3)
            vel = col1.number_input(
                "Flow / initial velocity (m/s)",
                min_value=0.0,
                help="Used for CdS and drag coefficient calculation.",
            )
            area = col2.number_input(
                "Reference area (m²)",
                min_value=0.0,
                help="Parachute reference area for drag coefficient (Cd = CdS / A).",
            )
            mass = col3.number_input(
                "Payload mass (kg)",
                min_value=0.0,
                help="Used for finite mass: F = m × a. Leave at 0 if not applicable.",
            )

            uploaded_files = st.file_uploader(
                "Attach result files",
                accept_multiple_files=True,
                help="Upload .dat files for infinite mass, or .csv files for finite mass.",
            )

            submit = st.form_submit_button("Create simulation", type="primary")

            if submit and name:
                sim = db.create_simulation(name, desc)
                db.update_simulation(
                    sim.id,
                    analysis_type=analysis_type,
                    velocity=vel if vel > 0 else None,
                    ref_area=area if area > 0 else None,
                    mass=mass if mass > 0 else None,
                )

                for f in uploaded_files:
                    content = f.read()
                    path, fmt, size, meta = storage.store_file(content, f.name, FileType.DRAG_RESULT, sim.id)
                    db.create_file(sim.id, f.name, path, FileType.DRAG_RESULT, fmt, size, meta)

                # Store confirmation details for display after rerun
                st.session_state["_sim_created"] = {
                    "name": name,
                    "type": analysis_type.replace("_", " ").title(),
                    "files": len(uploaded_files),
                    "velocity": vel if vel > 0 else None,
                    "ref_area": area if area > 0 else None,
                    "mass": mass if mass > 0 else None,
                }
                st.rerun()
            elif submit and not name:
                st.warning("Please enter a name.")

        # Show confirmation banner after successful creation
        if "_sim_created" in st.session_state:
            info = st.session_state.pop("_sim_created")
            st.success(f"Simulation **{info['name']}** created successfully!")
            details = f"**Type:** {info['type']}  •  **Files:** {info['files']}"
            if info["velocity"]:
                details += f"  •  **Velocity:** {info['velocity']} m/s"
            if info["ref_area"]:
                details += f"  •  **Ref Area:** {info['ref_area']} m²"
            if info["mass"]:
                details += f"  •  **Mass:** {info['mass']} kg"
            st.info(details)
            st.balloons()


    # ---------------------------------------------------------------------------
    # Tags Tab — create and delete global tags
    # ---------------------------------------------------------------------------
    with tabs[2]:
        st.subheader("Manage Tags")
        st.write("Tags are shared across all simulations. Create them here, then assign them on the Registry tab.")

        with st.form("new_tag"):
            col1, col2 = st.columns([3, 1])
            t_name = col1.text_input("Tag name")
            t_color = col2.color_picker("Color", "#3498db")
            if st.form_submit_button("Create tag"):
                if t_name:
                    db.create_tag(t_name, t_color)
                    st.rerun()
                else:
                    st.warning("Enter a tag name.")

        st.divider()
        tags = db.list_all_tags()
        if not tags:
            st.info("No tags yet.")
        else:
            for t in tags:
                col1, col2 = st.columns([5, 1])
                col1.markdown(
                    f'<span style="background:{t.color or "#ccc"};padding:3px 10px;border-radius:4px;color:#fff">'
                    f'🏷️ {t.name}</span>',
                    unsafe_allow_html=True,
                )
                if col2.button("🗑️ Delete", key=f"del_tag_{t.id}"):
                    db.delete_tag(t.id)
                    st.rerun()
