"""
AerisVault - UI Page Components
Streamlit page functions for database management and settings.
"""

import streamlit as st
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..database import SimulationDatabase
    from ..storage import StorageManager


def database_page(db: "SimulationDatabase", storage: "StorageManager"):
    """
    Display the database registry view with professional table layout.
    
    Args:
        db: Database manager instance
        storage: Storage manager instance
    """
    import pandas as pd
    
    sims = db.list_simulations()
    
    if not sims:
        st.info("📭 No simulations in the database yet. Go to **Manage Database** to add your first simulation.")
        return
    
    # Search/Filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search simulations", placeholder="Enter simulation name...", label_visibility="collapsed")
    with col2:
        st.write(f"**{len(sims)}** simulations")
    
    if search:
        sims = [s for s in sims if search.lower() in s.name.lower()]
    
    # Create table data
    table_data = []
    for sim in sims:
        files = db.get_files_by_simulation(sim.id)
        tags_str = ", ".join([t.name for t in sim.tags]) if sim.tags else "—"
        
        table_data.append({
            "ID": sim.id,
            "Name": sim.name,
            "Created": sim.created_at.strftime('%Y-%m-%d'),
            "Description": (sim.description[:50] + "...") if sim.description and len(sim.description) > 50 else (sim.description or "—"),
            "Tags": tags_str,
            "Files": len(files),
            "V (m/s)": f"{sim.velocity:.1f}" if sim.velocity else "—",
            "S (m²)": f"{sim.ref_area:.3f}" if sim.ref_area else "—",
        })
    
    df = pd.DataFrame(table_data)
    
    # Display as interactive table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Name": st.column_config.TextColumn("Simulation Name", width="medium"),
            "Created": st.column_config.TextColumn("Date", width="small"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Tags": st.column_config.TextColumn("Tags", width="medium"),
            "Files": st.column_config.NumberColumn("📁", width="small"),
            "V (m/s)": st.column_config.TextColumn("V (m/s)", width="small"),
            "S (m²)": st.column_config.TextColumn("S (m²)", width="small"),
        }
    )
    
    # Detail view for selected simulation
    st.divider()
    st.subheader("📋 Simulation Details")
    
    sim_names = [s.name for s in sims]
    selected_name = st.selectbox("Select simulation to view details:", sim_names, key="detail_sim_select")
    
    if selected_name:
        selected_sim = next(s for s in sims if s.name == selected_name)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"### {selected_sim.name}")
            st.write(selected_sim.description or "*No description*")
            
            # Tags
            if selected_sim.tags:
                tag_html = " ".join([f'<span style="background-color: {t.color or "#3498db"}; color: white; padding: 2px 8px; border-radius: 12px; margin-right: 4px; font-size: 12px;">{t.name}</span>' for t in selected_sim.tags])
                st.markdown(f"**Tags:** {tag_html}", unsafe_allow_html=True)
        
        with col2:
            st.metric("Velocity", f"{selected_sim.velocity or 'N/A'} m/s")
            st.metric("Reference Area", f"{selected_sim.ref_area or 'N/A'} m²")
            st.metric("Air Density", f"{selected_sim.air_density or 1.225} kg/m³")
        
        # Files section
        files = db.get_files_by_simulation(selected_sim.id)
        if files:
            st.write("**📁 Attached Files:**")
            for f in files:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📄 {f.original_filename}")
                with col2:
                    st.write(f"{f.file_size_bytes / 1024:.1f} KB")
                with col3:
                    st.write(f.file_type.value)
        else:
            st.info("No files attached to this simulation.")


def manage_database_page(db: "SimulationDatabase", storage: "StorageManager"):
    """
    Display the database management interface.
    
    Args:
        db: Database manager instance
        storage: Storage manager instance
    """
    st.subheader("✏️ Manage Database")
    
    tabs = st.tabs(["➕ Add Simulation", "✏️ Modify Simulation", "📤 Upload Files", "🏷️ Manage Tags", "🗑️ Delete"])
    
    # Add Simulation Tab
    with tabs[0]:
        st.write("### Create New Simulation")
        st.info("💡 You can attach result files immediately when creating a simulation.")
        
        # Simulation details
        name = st.text_input("Simulation Name", placeholder="e.g., Parachute_v1_mesh_fine", key="new_sim_name")
        description = st.text_area("Description", placeholder="Describe the simulation setup...", key="new_sim_desc")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            velocity = st.number_input("Velocity (m/s)", min_value=0.0, value=0.0, key="new_sim_vel")
        with col2:
            ref_area = st.number_input("Reference Area (m²)", min_value=0.0, value=0.0, key="new_sim_area")
        with col3:
            air_density = st.number_input("Air Density (kg/m³)", min_value=0.0, value=1.225, key="new_sim_density")
        
        # File upload section
        st.write("#### 📎 Attach Result Files (Optional)")
        uploaded_files = st.file_uploader(
            "Upload ICFD Drag Files", 
            type=['dat', 'txt'],
            accept_multiple_files=True,
            key="new_sim_files"
        )
        
        if uploaded_files:
            st.write(f"📁 {len(uploaded_files)} file(s) ready to attach:")
            for f in uploaded_files:
                st.write(f"  - {f.name}")
        
        # Create button
        if st.button("✅ Create Simulation", type="primary"):
            if not name:
                st.error("Please provide a simulation name.")
            else:
                try:
                    # Create simulation
                    sim = db.create_simulation(name=name, description=description)
                    db.update_simulation(
                        sim.id,
                        velocity=velocity if velocity > 0 else None,
                        ref_area=ref_area if ref_area > 0 else None,
                        air_density=air_density
                    )
                    
                    # Process uploaded files
                    files_processed = 0
                    for uploaded_file in uploaded_files:
                        try:
                            from ..models import FileType
                            file_content = uploaded_file.read()
                            
                            storage_path, fmt, size, metadata = storage.store_file(
                                file_content,
                                uploaded_file.name,
                                FileType.DRAG_RESULT,
                                sim.id
                            )
                            
                            db.create_file(
                                simulation_id=sim.id,
                                filename=uploaded_file.name,
                                file_type=FileType.DRAG_RESULT,
                                storage_format=fmt,
                                storage_path=storage_path,
                                size_bytes=size,
                                metadata_json=metadata
                            )
                            files_processed += 1
                        except Exception as e:
                            st.warning(f"⚠️ Could not process {uploaded_file.name}: {e}")
                    
                    if files_processed > 0:
                        st.success(f"✅ Created simulation '{name}' with {files_processed} file(s) attached!")
                    else:
                        st.success(f"✅ Created simulation: {name}")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating simulation: {e}")
    
    # Modify Simulation Tab
    with tabs[1]:
        st.write("### Modify Existing Simulation")
        
        sims = db.list_simulations()
        if not sims:
            st.info("📭 No simulations to modify. Create one first.")
        else:
            # Simulation selector
            sim_names = [s.name for s in sims]
            selected_name = st.selectbox(
                "Select Simulation to Modify", 
                sim_names, 
                key="modify_sim_select"
            )
            selected_sim = next(s for s in sims if s.name == selected_name)
            
            st.divider()
            
            # --- Properties Section ---
            st.write("#### 📝 Properties")
            
            with st.form(f"modify_sim_form_{selected_sim.id}"):
                new_name = st.text_input("Name", value=selected_sim.name, key=f"mod_name_{selected_sim.id}")
                new_description = st.text_area(
                    "Description", 
                    value=selected_sim.description or "", 
                    key=f"mod_desc_{selected_sim.id}"
                )
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_velocity = st.number_input(
                        "Velocity (m/s)", 
                        min_value=0.0, 
                        value=float(selected_sim.velocity or 0.0), 
                        key=f"mod_vel_{selected_sim.id}"
                    )
                with col2:
                    new_ref_area = st.number_input(
                        "Reference Area (m²)", 
                        min_value=0.0, 
                        value=float(selected_sim.ref_area or 0.0), 
                        key=f"mod_area_{selected_sim.id}"
                    )
                with col3:
                    new_air_density = st.number_input(
                        "Air Density (kg/m³)", 
                        min_value=0.0, 
                        value=float(selected_sim.air_density or 1.225), 
                        key=f"mod_density_{selected_sim.id}"
                    )
                
                if st.form_submit_button("💾 Save Properties", type="primary"):
                    try:
                        db.update_simulation(
                            selected_sim.id,
                            name=new_name,
                            description=new_description,
                            velocity=new_velocity if new_velocity > 0 else None,
                            ref_area=new_ref_area if new_ref_area > 0 else None,
                            air_density=new_air_density
                        )
                        st.success(f"✅ Simulation '{new_name}' updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating simulation: {e}")
            
            st.divider()
            
            # --- Tags Section ---
            st.write("#### 🏷️ Tags")
            
            # Show current tags
            current_tags = [t.name for t in selected_sim.tags] if selected_sim.tags else []
            if current_tags:
                tag_html = " ".join([
                    f'<span style="background-color: {t.color or "#3498db"}; color: white; padding: 2px 8px; border-radius: 12px; margin-right: 4px; font-size: 12px;">{t.name}</span>' 
                    for t in selected_sim.tags
                ])
                st.markdown(f"**Current tags:** {tag_html}", unsafe_allow_html=True)
            else:
                st.write("*No tags assigned*")
            
            # Add tags
            all_tags = db.list_all_tags()
            available_tags = [t.name for t in all_tags if t.name not in current_tags]
            
            col1, col2 = st.columns([3, 1])
            with col1:
                tags_to_add = st.multiselect(
                    "Add Tags", 
                    options=available_tags, 
                    key=f"mod_add_tags_{selected_sim.id}"
                )
            with col2:
                if st.button("➕ Add Selected Tags", key="mod_add_tags_btn"):
                    if tags_to_add:
                        try:
                            db.add_tags_to_simulation(selected_sim.id, tags_to_add)
                            st.success(f"✅ Added {len(tags_to_add)} tag(s)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            st.divider()
            
            # --- Files Section ---
            st.write("#### 📁 Attached Files")
            
            files = db.get_files_by_simulation(selected_sim.id)
            if files:
                for f in files:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    with col1:
                        st.write(f"📄 {f.original_filename}")
                    with col2:
                        st.write(f"{f.file_size_bytes / 1024:.1f} KB")
                    with col3:
                        st.write(f.file_type.value)
                    with col4:
                        if st.button("🗑️", key=f"del_file_{f.id}"):
                            try:
                                storage.delete_file(f.storage_path)
                                db.delete_file(f.id)
                                st.success(f"Deleted: {f.original_filename}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.info("No files attached.")
            
            # Upload new files
            st.write("**Add New Files:**")
            new_files = st.file_uploader(
                "Upload ICFD Drag Files",
                type=['dat', 'txt'],
                accept_multiple_files=True,
                key="mod_upload_files"
            )
            
            if new_files and st.button("📤 Upload Files", key="mod_upload_btn"):
                from ..models import FileType
                files_processed = 0
                for uploaded_file in new_files:
                    try:
                        file_content = uploaded_file.read()
                        storage_path, fmt, size, metadata = storage.store_file(
                            file_content,
                            uploaded_file.name,
                            FileType.DRAG_RESULT,
                            selected_sim.id
                        )
                        db.create_file(
                            simulation_id=selected_sim.id,
                            filename=uploaded_file.name,
                            file_type=FileType.DRAG_RESULT,
                            storage_format=fmt,
                            storage_path=storage_path,
                            size_bytes=size,
                            metadata_json=metadata
                        )
                        files_processed += 1
                    except Exception as e:
                        st.warning(f"⚠️ Could not process {uploaded_file.name}: {e}")
                
                if files_processed > 0:
                    st.success(f"✅ Uploaded {files_processed} file(s)!")
                    st.rerun()
    
    # Upload Files Tab
    with tabs[2]:
        st.write("### Upload Result Files")
        
        sims = db.list_simulations()
        if not sims:
            st.warning("Create a simulation first before uploading files.")
        else:
            sim_name = st.selectbox("Select Simulation", [s.name for s in sims])
            
            uploaded_file = st.file_uploader("Upload ICFD Drag File", type=['dat', 'txt'])
            
            if uploaded_file and st.button("Process & Store"):
                from ..models import FileType
                
                selected_sim = next(s for s in sims if s.name == sim_name)
                file_content = uploaded_file.read()
                
                try:
                    storage_path, fmt, size, metadata = storage.store_file(
                        file_content,
                        uploaded_file.name,
                        FileType.DRAG_RESULT,
                        selected_sim.id
                    )
                    
                    db.create_file(
                        simulation_id=selected_sim.id,
                        filename=uploaded_file.name,
                        file_type=FileType.DRAG_RESULT,
                        storage_format=fmt,
                        storage_path=storage_path,
                        size_bytes=size,
                        metadata_json=metadata
                    )
                    
                    st.success(f"✅ File uploaded and stored successfully!")
                except Exception as e:
                    st.error(f"Error processing file: {e}")
    
    # Manage Tags Tab
    with tabs[3]:
        st.write("### Tag Management")
        
        # Create new tag
        with st.form("new_tag_form"):
            tag_name = st.text_input("New Tag Name")
            tag_color = st.color_picker("Tag Color", "#3498db")
            
            if st.form_submit_button("Create Tag"):
                if tag_name:
                    try:
                        db.create_tag(name=tag_name, color=tag_color)
                        st.success(f"✅ Created tag: {tag_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # List existing tags
        st.write("#### Existing Tags")
        tags = db.list_all_tags()
        for tag in tags:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"🏷️ **{tag.name}** ({len(tag.simulations)} simulations)")
            with col2:
                if st.button("🗑️", key=f"del_tag_{tag.id}"):
                    db.delete_tag(tag.id)
                    st.rerun()
    
    # Delete Tab
    with tabs[4]:
        st.write("### Delete Simulations")
        st.warning("⚠️ Deletion is permanent and cannot be undone.")
        
        sims = db.list_simulations()
        for sim in sims:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{sim.name}** - {sim.created_at.strftime('%Y-%m-%d')}")
            with col2:
                if st.button("Delete", key=f"del_sim_{sim.id}"):
                    db.delete_simulation(sim.id)
                    st.success(f"Deleted: {sim.name}")
                    st.rerun()


def settings_page(db: "SimulationDatabase"):
    """
    Display the settings page.
    
    Args:
        db: Database manager instance
    """
    from ..config import get_settings
    
    st.title("⚙️ Settings")
    st.markdown("Configure AerisVault application settings.")
    
    settings = get_settings()
    
    # Filter Settings
    st.subheader("🔧 Filter Settings")
    
    with st.form("filter_settings_form"):
        enable_filter = st.checkbox(
            "Enable filtering by default",
            value=settings.filter_settings.enabled_by_default
        )
        
        filter_type = st.selectbox(
            "Default filter type",
            ["savgol", "moving_average", "lowpass"],
            index=["savgol", "moving_average", "lowpass"].index(
                settings.filter_settings.default_filter_type
            )
        )
        
        col1, col2 = st.columns(2)
        with col1:
            savgol_window = st.number_input(
                "Savgol window length",
                value=settings.filter_settings.savgol_window_length,
                min_value=5,
                step=2
            )
            savgol_poly = st.number_input(
                "Savgol polynomial order",
                value=settings.filter_settings.savgol_polyorder,
                min_value=1,
                max_value=5
            )
        with col2:
            moving_avg_window = st.number_input(
                "Moving average window",
                value=settings.filter_settings.moving_avg_window,
                min_value=2
            )
            lowpass_cutoff = st.number_input(
                "Lowpass cutoff frequency (Hz)",
                value=settings.filter_settings.lowpass_cutoff_freq,
                min_value=0.1
            )
        
        if st.form_submit_button("Save Filter Settings"):
            settings.filter_settings.enabled_by_default = enable_filter
            settings.filter_settings.default_filter_type = filter_type
            settings.filter_settings.savgol_window_length = int(savgol_window)
            settings.filter_settings.savgol_polyorder = int(savgol_poly)
            settings.filter_settings.moving_avg_window = int(moving_avg_window)
            settings.filter_settings.lowpass_cutoff_freq = float(lowpass_cutoff)
            settings.save()
            st.success("✅ Settings saved!")
    
    # Plot Settings
    st.subheader("📊 Plot Settings")
    
    with st.form("plot_settings_form"):
        theme = st.selectbox(
            "Plot theme",
            ["plotly_white", "plotly_dark", "plotly", "simple_white"],
            index=["plotly_white", "plotly_dark", "plotly", "simple_white"].index(
                settings.plot_settings.theme
            )
        )
        
        col1, col2 = st.columns(2)
        with col1:
            width = st.number_input("Default width", value=settings.plot_settings.width, min_value=400)
            line_width = st.number_input("Line width", value=settings.plot_settings.line_width, min_value=1)
        with col2:
            height = st.number_input("Default height", value=settings.plot_settings.height, min_value=300)
            font_size = st.number_input("Font size", value=settings.plot_settings.font_size, min_value=8)
        
        show_grid = st.checkbox("Show grid", value=settings.plot_settings.show_grid)
        
        if st.form_submit_button("Save Plot Settings"):
            settings.plot_settings.theme = theme
            settings.plot_settings.width = int(width)
            settings.plot_settings.height = int(height)
            settings.plot_settings.line_width = int(line_width)
            settings.plot_settings.font_size = int(font_size)
            settings.plot_settings.show_grid = show_grid
            settings.save()
            st.success("✅ Settings saved!")
    
    # Storage Info
    st.subheader("💾 Storage Information")
    st.write(f"**Data directory:** `{settings.data_dir}`")
    st.write(f"**Max file size:** {settings.max_file_size_mb} MB")
