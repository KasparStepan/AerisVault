"""
AerisVault - Single Simulation Analysis Page
Detailed analysis of individual simulation files.
Uses session state to persist data across widget interactions.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aerisvault.parsers import LSDynaICFDDragParser
from aerisvault.plotting.single_plot import SinglePlotter
from aerisvault.analysis.statistics import StatisticalAnalyzer
from aerisvault.analysis.event_detection import EventDetector
from aerisvault.filters import DataFilter
from aerisvault.database import SimulationDatabase
from aerisvault.storage import StorageManager
from aerisvault.models import FileType

st.set_page_config(page_title="Single Analysis", page_icon="📊", layout="wide")

st.title("📊 Single Simulation Analysis")
st.markdown("Deep dive into individual simulation results with advanced analysis tools.")

# Initialize session state for persistent data
if 'analysis_df' not in st.session_state:
    st.session_state.analysis_df = None
if 'analysis_source' not in st.session_state:
    st.session_state.analysis_source = None
if 'sim_velocity' not in st.session_state:
    st.session_state.sim_velocity = None
if 'sim_ref_area' not in st.session_state:
    st.session_state.sim_ref_area = None
if 'sim_air_density' not in st.session_state:
    st.session_state.sim_air_density = 1.225

# Initialize components
parser = LSDynaICFDDragParser()
plotter = SinglePlotter()
analyzer = StatisticalAnalyzer()
db = SimulationDatabase()
storage = StorageManager()

# Data source selection
st.subheader("📂 Select Data Source")
data_source = st.radio(
    "Choose how to load simulation data:",
    ["🗄️ From Database", "📤 Upload File"],
    horizontal=True,
    key="data_source_radio"
)

# Show current loaded data status
if st.session_state.analysis_df is not None:
    st.success(f"✅ Data loaded: **{st.session_state.analysis_source}** ({len(st.session_state.analysis_df)} points)")
    if st.button("🗑️ Clear loaded data"):
        st.session_state.analysis_df = None
        st.session_state.analysis_source = None
        st.session_state.sim_velocity = None
        st.session_state.sim_ref_area = None
        st.rerun()

st.divider()

if data_source == "🗄️ From Database":
    sims = db.list_simulations()
    sims_with_files = []
    
    for sim in sims:
        files = db.get_files_by_simulation(sim.id)
        result_files = [f for f in files if f.file_type == FileType.DRAG_RESULT]
        if result_files:
            sims_with_files.append((sim, result_files))
    
    if not sims_with_files:
        st.info("📭 No simulations with result files in the database.")
    else:
        sim_options = {f"{sim.name} ({len(files)} file{'s' if len(files) > 1 else ''})": (sim, files) 
                       for sim, files in sims_with_files}
        
        selected_sim_name = st.selectbox("Select Simulation", list(sim_options.keys()), key="sim_select")
        
        if selected_sim_name:
            selected_sim, result_files = sim_options[selected_sim_name]
            
            if len(result_files) > 1:
                file_options = {f.original_filename: f for f in result_files}
                selected_file_name = st.selectbox("Select Result File", list(file_options.keys()), key="file_select")
                selected_file = file_options[selected_file_name]
            else:
                selected_file = result_files[0]
                st.write(f"📄 File: **{selected_file.original_filename}**")
            
            with st.expander("📋 Simulation Details"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Velocity", f"{selected_sim.velocity or 'N/A'} m/s")
                with col2:
                    st.metric("Ref Area", f"{selected_sim.ref_area or 'N/A'} m²")
                with col3:
                    st.metric("Air Density", f"{selected_sim.air_density or 1.225} kg/m³")
            
            if st.button("📥 Load Simulation Data", type="primary"):
                try:
                    st.session_state.analysis_df = storage.load_result_data(selected_file.storage_path)
                    st.session_state.analysis_source = f"{selected_sim.name} / {selected_file.original_filename}"
                    st.session_state.sim_velocity = selected_sim.velocity
                    st.session_state.sim_ref_area = selected_sim.ref_area
                    st.session_state.sim_air_density = selected_sim.air_density or 1.225
                    st.success(f"✅ Loaded {len(st.session_state.analysis_df)} data points")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error loading data: {str(e)}")

else:  # Upload File
    uploaded_file = st.file_uploader("Upload ICFD Drag File", type=['dat', 'txt'], key="file_uploader")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        upload_velocity = st.number_input("Velocity (m/s)", min_value=0.0, value=0.0, key="upload_vel")
    with col2:
        upload_ref_area = st.number_input("Reference Area (m²)", min_value=0.0, value=0.0, key="upload_area")
    with col3:
        upload_air_density = st.number_input("Air Density (kg/m³)", min_value=0.0, value=1.225, key="upload_density")
    
    if uploaded_file is not None:
        if st.button("📥 Load File", type="primary"):
            try:
                file_content = uploaded_file.read()
                st.session_state.analysis_df = parser.parse(file_content)
                st.session_state.analysis_source = uploaded_file.name
                st.session_state.sim_velocity = upload_velocity if upload_velocity > 0 else None
                st.session_state.sim_ref_area = upload_ref_area if upload_ref_area > 0 else None
                st.session_state.sim_air_density = upload_air_density
                st.success(f"✅ Loaded {len(st.session_state.analysis_df)} data points")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error parsing file: {str(e)}")

# Analysis section (shown when data is loaded)
if st.session_state.analysis_df is not None:
    df = st.session_state.analysis_df
    
    st.divider()
    st.subheader("📊 Analysis")
    
    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Plots", "📊 Statistics", "🎯 Events", "🪂 CdS Analysis"])
    
    with tab1:
        st.subheader("Interactive Visualization")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Plot type selection
            plot_type = st.selectbox(
                "Plot Type",
                ["Forces (Pressure)", "Forces (Viscous)", "Moments (Pressure)", "Resultant Force", "3D Trajectory", "CdS over Time"],
                key="plot_type"
            )
            
            # Filter controls
            st.write("**Filter Settings**")
            enable_filter = st.checkbox("Enable Filtering", value=False, key="enable_filter")
            
            filter_params = None
            if enable_filter:
                filter_type = st.selectbox("Filter Type", ["savgol", "moving_average", "lowpass"], key="filter_type")
                
                if filter_type == "savgol":
                    window = st.slider("Window Length", 5, 201, 51, 2, key="savgol_window")
                    polyorder = st.slider("Polynomial Order", 1, 5, 3, key="savgol_poly")
                    filter_params = {'filter_type': filter_type, 'window_length': window, 'polyorder': polyorder}
                elif filter_type == "moving_average":
                    window = st.slider("Window Size", 3, 100, 10, key="ma_window")
                    filter_params = {'filter_type': filter_type, 'window': window}
                else:
                    cutoff = st.slider("Cutoff Frequency (Hz)", 0.1, 50.0, 10.0, key="lp_cutoff")
                    order = st.slider("Filter Order", 1, 8, 4, key="lp_order")
                    filter_params = {'filter_type': filter_type, 'cutoff_freq': cutoff, 'order': order}
        
        with col2:
            try:
                if plot_type == "Forces (Pressure)":
                    fig = plotter.plot_forces(df, ['Fpx', 'Fpy', 'Fpz'], "Pressure Forces", enable_filter, filter_params)
                elif plot_type == "Forces (Viscous)":
                    fig = plotter.plot_forces(df, ['Fvx', 'Fvy', 'Fvz'], "Viscous Forces", enable_filter, filter_params)
                elif plot_type == "Moments (Pressure)":
                    fig = plotter.plot_moments(df, ['Mpx', 'Mpy', 'Mpz'], "Pressure Moments", enable_filter, filter_params)
                elif plot_type == "Resultant Force":
                    fig = plotter.plot_resultant_force(df, enable_filter=enable_filter, filter_params=filter_params)
                elif plot_type == "CdS over Time":
                    # CdS = -Fpz / (0.5 * rho * V^2)
                    # Note: Fpz is in OPPOSITE direction, so we use -Fpz for drag
                    velocity = st.session_state.sim_velocity
                    rho = st.session_state.sim_air_density
                    
                    if velocity and velocity > 0:
                        dynamic_pressure = 0.5 * rho * velocity**2
                        cds = -df['Fpz'] / dynamic_pressure  # Negative because drag is opposite to flow
                        
                        import plotly.graph_objects as go
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df['time'], y=cds,
                            mode='lines', name='CdS',
                            line=dict(width=2)
                        ))
                        
                        if enable_filter and filter_params:
                            filter_type = filter_params.get('filter_type', 'savgol')
                            params_copy = {k: v for k, v in filter_params.items() if k != 'filter_type'}
                            cds_filtered = DataFilter.apply_filter(cds, df['time'], filter_type, **params_copy)
                            fig.add_trace(go.Scatter(
                                x=df['time'], y=cds_filtered,
                                mode='lines', name='CdS (filtered)',
                                line=dict(width=2)
                            ))
                        
                        fig.update_layout(
                            title="CdS (Drag Coefficient × Reference Area) over Time",
                            xaxis_title="Time (s)",
                            yaxis_title="CdS (m²)",
                            hovermode='x unified'
                        )
                    else:
                        st.warning("⚠️ Velocity not set. Please specify velocity to calculate CdS.")
                        fig = None
                else:
                    fig = plotter.plot_3d_force_trajectory(df)
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Export buttons
                    st.write("**📤 Export Plot**")
                    col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
                    
                    with col_exp1:
                        # PNG export
                        try:
                            import kaleido
                            img_bytes = fig.to_image(format="png", width=1200, height=600, scale=2)
                            st.download_button(
                                "📷 PNG",
                                data=img_bytes,
                                file_name=f"{plot_type.replace(' ', '_').lower()}.png",
                                mime="image/png"
                            )
                        except ImportError:
                            st.button("📷 PNG", disabled=True, help="Install kaleido: pip install kaleido")
                        except Exception as e:
                            st.button("📷 PNG", disabled=True, help=f"Export error: {str(e)[:50]}")
                    
                    with col_exp2:
                        # SVG export
                        try:
                            import kaleido
                            svg_bytes = fig.to_image(format="svg", width=1200, height=600)
                            st.download_button(
                                "🎨 SVG",
                                data=svg_bytes,
                                file_name=f"{plot_type.replace(' ', '_').lower()}.svg",
                                mime="image/svg+xml"
                            )
                        except ImportError:
                            st.button("🎨 SVG", disabled=True, help="Install kaleido: pip install kaleido")
                        except Exception as e:
                            st.button("🎨 SVG", disabled=True, help=f"Export error: {str(e)[:50]}")
                    
                    with col_exp3:
                        # HTML export
                        html_str = fig.to_html(include_plotlyjs="cdn")
                        st.download_button(
                            "🌐 HTML",
                            data=html_str,
                            file_name=f"{plot_type.replace(' ', '_').lower()}.html",
                            mime="text/html"
                        )
                    
                    with col_exp4:
                        # JSON export
                        json_str = fig.to_json()
                        st.download_button(
                            "📊 JSON",
                            data=json_str,
                            file_name=f"{plot_type.replace(' ', '_').lower()}.json",
                            mime="application/json"
                        )
            except Exception as e:
                st.error(f"Error generating plot: {str(e)}")
    
    with tab2:
        st.subheader("Statistical Analysis")
        
        available_cols = [c for c in df.columns if c != 'time']
        default_cols = [c for c in ['Fpx', 'Fpy', 'Fpz'] if c in available_cols]
        
        selected_cols = st.multiselect(
            "Select Columns",
            available_cols,
            default=default_cols,
            key="stats_cols"
        )
        
        if selected_cols:
            stats = analyzer.basic_statistics(df, selected_cols)
            st.dataframe(stats, use_container_width=True)
            
            csv = stats.to_csv()
            st.download_button("📥 Download Statistics", csv, "statistics.csv", "text/csv")
    
    with tab3:
        st.subheader("Event Detection")
        
        force_options = [c for c in ['Fpz', 'Fpx', 'Fpy'] if c in df.columns]
        force_col = st.selectbox("Force Column", force_options, key="event_col") if force_options else None
        
        if force_col and st.button("🔍 Detect Events"):
            try:
                events = EventDetector.auto_detect_events(df, force_col)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if events['deployment'].get('detected'):
                        st.success("✅ Deployment Detected")
                        st.metric("Time", f"{events['deployment']['deployment_time']:.4f} s")
                        st.metric("Force", f"{events['deployment']['deployment_force']:.2f} N")
                
                with col2:
                    if events['steady_state'].get('detected'):
                        st.success("✅ Steady State Reached")
                        st.metric("Time", f"{events['steady_state']['steady_time']:.4f} s")
                        st.metric("Value", f"{events['steady_state']['steady_value']:.2f} N")
                
                if 'inflation' in events:
                    st.info("💨 Inflation Analysis")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Start", f"{events['inflation']['start_time']:.4f} s")
                    with col2:
                        st.metric("Peak", f"{events['inflation']['peak_time']:.4f} s")
                    with col3:
                        st.metric("Duration", f"{events['inflation']['inflation_duration']:.4f} s")
            except Exception as e:
                st.error(f"Error detecting events: {str(e)}")
    
    with tab4:
        st.subheader("🪂 CdS Analysis (Drag Coefficient × Area)")
        
        st.info("""
        **CdS Calculation:**
        - CdS = -Fpz / (0.5 × ρ × V²)
        - Note: Fpz is in the **opposite direction** to flow, so we use **-Fpz** for drag force
        - Result is Cd × S (m²), not dimensionless Cd
        """)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            cds_velocity = st.number_input(
                "Velocity V (m/s)", 
                min_value=0.1, 
                value=float(st.session_state.sim_velocity or 10.0),
                key="cds_velocity"
            )
        with col2:
            cds_rho = st.number_input(
                "Air Density ρ (kg/m³)", 
                min_value=0.1, 
                value=float(st.session_state.sim_air_density or 1.225),
                key="cds_rho"
            )
        with col3:
            dynamic_pressure = 0.5 * cds_rho * cds_velocity**2
            st.metric("Dynamic Pressure q (Pa)", f"{dynamic_pressure:.2f}")
        
        if cds_velocity > 0:
            # Calculate CdS using -Fpz (opposite direction)
            cds_series = -df['Fpz'] / dynamic_pressure
            
            # Statistics
            st.write("### CdS Statistics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean CdS", f"{cds_series.mean():.4f} m²")
            with col2:
                st.metric("Max CdS", f"{cds_series.max():.4f} m²")
            with col3:
                st.metric("Min CdS", f"{cds_series.min():.4f} m²")
            with col4:
                st.metric("Std Dev", f"{cds_series.std():.4f} m²")
            
            # Time window analysis
            st.write("### Time Window Analysis")
            
            # Get time bounds from simulation
            t_min = float(df['time'].min())
            t_max = float(df['time'].max())
            
            # Initialize session state for time window if not exists
            if 'cds_t_start' not in st.session_state:
                st.session_state.cds_t_start = t_max * 0.5
            if 'cds_t_end' not in st.session_state:
                st.session_state.cds_t_end = t_max
            
            # Callbacks for synchronization
            def on_slider_change():
                st.session_state.cds_t_start = st.session_state.cds_slider_key[0]
                st.session_state.cds_t_end = st.session_state.cds_slider_key[1]
            
            def on_start_input_change():
                st.session_state.cds_t_start = st.session_state.cds_start_input_key
            
            def on_end_input_change():
                st.session_state.cds_t_end = st.session_state.cds_end_input_key
            
            # Visual range slider for time window
            st.slider(
                "Select Time Window",
                min_value=t_min,
                max_value=t_max,
                value=(st.session_state.cds_t_start, st.session_state.cds_t_end),
                step=(t_max - t_min) / 1000,
                format="%.4f s",
                key="cds_slider_key",
                on_change=on_slider_change
            )
            
            # Direct number inputs for precise control
            col1, col2 = st.columns(2)
            with col1:
                st.number_input(
                    "Start Time (s)",
                    min_value=t_min,
                    max_value=t_max,
                    value=st.session_state.cds_t_start,
                    format="%.4f",
                    key="cds_start_input_key",
                    on_change=on_start_input_change
                )
            with col2:
                st.number_input(
                    "End Time (s)",
                    min_value=t_min,
                    max_value=t_max,
                    value=st.session_state.cds_t_end,
                    format="%.4f",
                    key="cds_end_input_key",
                    on_change=on_end_input_change
                )
            
            t_start = st.session_state.cds_t_start
            t_end = st.session_state.cds_t_end
            
            # Visual representation of the selected interval
            interval_pct = ((t_end - t_start) / (t_max - t_min)) * 100 if t_max > t_min else 100
            st.caption(f"📏 Selected interval: **{t_start:.4f}s** to **{t_end:.4f}s** ({interval_pct:.1f}% of total time)")
            
            # Calculate statistics for selected window
            mask = (df['time'] >= t_start) & (df['time'] <= t_end)
            if mask.any():
                cds_window = cds_series[mask]
                fpz_window = df['Fpz'][mask]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(f"Mean CdS", f"{cds_window.mean():.4f} m²")
                with col2:
                    st.metric(f"Mean Drag Force", f"{-fpz_window.mean():.2f} N")
                with col3:
                    st.metric(f"Points in Window", f"{mask.sum()}")
            
            st.divider()
            
            # --- Cd Calculation from CdS ---
            st.write("### Cd Calculation (from CdS)")
            st.info("💡 **Cd = CdS / S** — Enter reference area S to calculate dimensionless drag coefficient Cd")
            
            col1, col2 = st.columns(2)
            with col1:
                ref_area_cd = st.number_input(
                    "Reference Area S (m²)",
                    min_value=0.001,
                    value=float(st.session_state.sim_ref_area or 1.0),
                    format="%.4f",
                    key="cd_ref_area"
                )
            with col2:
                if ref_area_cd > 0:
                    # Calculate Cd for the selected time window
                    if mask.any():
                        mean_cds = cds_window.mean()
                        mean_cd = mean_cds / ref_area_cd
                        st.metric("Mean Cd (in window)", f"{mean_cd:.4f}")
            
            # Full Cd time series
            if ref_area_cd > 0:
                cd_series = cds_series / ref_area_cd
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Mean Cd (full)", f"{cd_series.mean():.4f}")
                with col2:
                    st.metric("Max Cd", f"{cd_series.max():.4f}")
                with col3:
                    st.metric("Min Cd", f"{cd_series.min():.4f}")
                with col4:
                    st.metric("Std Dev Cd", f"{cd_series.std():.4f}")
            
            st.divider()
            
            # Export CdS data
            cds_df = pd.DataFrame({
                'time': df['time'],
                'Fpz': df['Fpz'],
                'CdS': cds_series,
                'Cd': cds_series / ref_area_cd if ref_area_cd > 0 else np.nan
            })
            csv = cds_df.to_csv(index=False)
            st.download_button("📥 Download CdS/Cd Data", csv, "cds_cd_analysis.csv", "text/csv")
