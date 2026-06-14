"""
AerisVault UI - Simulation Comparison
Compare multiple simulations side-by-side using dynaprocessing.
"""

import streamlit as st
import pandas as pd
from dynaprocessing.models.curve import Curve
from dynaprocessing.models.infinite_mass import InfiniteMassSimulation
from dynaprocessing.models.finite_mass import FiniteMassSimulation
from dynaprocessing.viz.plot_utils import plot_curves_plotly
from dynaprocessing.analysis.comparison import align_curves, calculate_rmse, compare_statistics
from aerisvault.modules.fsi.ui.components import sidebar_filter_settings, sidebar_plot_style
from aerisvault.modules.fsi.core.bootstrap import ensure_initialized


def render():
    ensure_initialized()
    db = st.session_state["fsi.db"]
    storage = st.session_state["fsi.storage"]

    st.title("📈 Simulation Comparison")

    # --- 1. Select simulations ---
    sims = db.list_simulations()
    if not sims:
        st.warning("No simulations in the database yet.")
        st.stop()

    selected_names = st.multiselect(
        "Select simulations to compare (2 or more):",
        options=[s.name for s in sims],
    )
    selected_sims = [s for s in sims if s.name in selected_names]

    if len(selected_sims) < 2:
        st.info("Select at least 2 simulations to begin comparison.")
        st.stop()

    # Warn if user mixes infinite and finite mass — the curves will be different
    types_in_selection = {s.analysis_type for s in selected_sims}
    if len(types_in_selection) > 1:
        st.warning(
            "You have selected a mix of Infinite Mass and Finite Mass simulations. "
            "Their result curves are different (forces vs. kinematics) and may not be comparable."
        )

    # --- 2. Sidebar controls ---
    filter_params = sidebar_filter_settings()
    plot_style = sidebar_plot_style()

    # --- 3. Load all curves from each simulation ---
    # We collect every simulation's available curve names so the user can pick which one to compare.
    all_sim_curves: dict = {}  # {sim_name: {curve_name: Curve}}

    for sim in selected_sims:
        files = db.get_files_by_simulation(sim.id)
        drag_files = [f for f in files if f.file_type.value == "drag_result"]

        if not drag_files:
            st.warning(f"No result files found for '{sim.name}'. Skipping.")
            continue

        sim_dir = storage.base_dir / "raw" / f"sim_{sim.id}"

        try:
            if sim.analysis_type == "infinite_mass":
                sim_model = InfiniteMassSimulation(directory_path=sim_dir)
                # Flat dict: {curve_name: Curve}
                curves_for_sim = sim_model.curves

            else:
                sim_model = FiniteMassSimulation(directory_path=sim_dir)
                # Nested dict: {node_id: {curve_name: Curve}} — flatten, keeping first match per name
                curves_for_sim = {}
                for node_curves in sim_model.curves.values():
                    for curve_name, curve in node_curves.items():
                        if curve_name not in curves_for_sim:
                            curves_for_sim[curve_name] = curve

        except FileNotFoundError:
            st.warning(f"Directory not found for '{sim.name}': `{sim_dir}`")
            continue

        all_sim_curves[sim.name] = curves_for_sim

    if len(all_sim_curves) < 2:
        st.error("Could not load curves from at least 2 simulations.")
        st.stop()

    # --- 3b. Compute derived quantities (resultant force, CdS) ---
    # Build a lookup from sim name to DB record for velocity/density
    sim_db_lookup = {s.name: s for s in selected_sims}

    for sim_name, curves_for_sim in all_sim_curves.items():
        sim_record = sim_db_lookup[sim_name]

        # Resultant force from Fpx, Fpy, Fpz (infinite mass)
        fpx = curves_for_sim.get("Fpx")
        fpy = curves_for_sim.get("Fpy")
        fpz = curves_for_sim.get("Fpz")
        if fpx and fpy and fpz:
            resultant_curve = Curve.resultant(fpx, fpy, fpz)
            curves_for_sim["resultant_force"] = resultant_curve

        # CdS from each force component + resultant (infinite mass with known velocity)
        if sim_record.analysis_type == "infinite_mass" and sim_record.velocity and sim_record.velocity > 0:
            rho = sim_record.air_density
            v = sim_record.velocity
            for force_name in ("Fpx", "Fpy", "Fpz", "resultant_force"):
                force_curve = curves_for_sim.get(force_name)
                if force_curve:
                    cds_curve = force_curve.calculate_cds(v=v, rho=rho)
                    curves_for_sim[cds_curve.name] = cds_curve

    # --- 4. Let user pick which curve/property to compare ---
    # Find curve names that appear in ALL selected simulations (intersection)
    available_curve_names = set.intersection(*[set(curves.keys()) for curves in all_sim_curves.values()])

    if not available_curve_names:
        st.error(
            "No common curve names found across the selected simulations. "
            "Make sure the result files have at least one column in common (e.g. 'Fpz')."
        )
        st.stop()

    selected_curve_name = st.selectbox(
        "Select property to compare:",
        sorted(available_curve_names),
        help="Only properties found in all selected simulations are shown.",
    )

    # --- 5. Extract and filter the chosen curve from each simulation ---
    comparison_curves = []
    for sim_name, curves_dict in all_sim_curves.items():
        curve = curves_dict[selected_curve_name]

        # Create a copy with the simulation name — so the plot legend shows the simulation
        # name (e.g. "cross_2m_6ms") instead of the column name (e.g. "Fpz")
        curve_renamed = Curve(
            time=curve.time,
            values=curve.values,
            name=sim_name,
            units=curve.units,
            filter_history=list(curve.filter_history),
        )

        # Apply filter if enabled
        if filter_params["enabled"]:
            filter_type = filter_params["type"]
            if filter_type == "cfc":
                curve_renamed = curve_renamed.apply_cfc_filter(cfc=filter_params["cfc"])
            elif filter_type == "butterworth":
                curve_renamed = curve_renamed.apply_butterworth_filter(cutoff_freq=filter_params["cutoff"])
            elif filter_type == "moving_average":
                curve_renamed = curve_renamed.apply_moving_average_filter(window_size=filter_params["window"])
            elif filter_type == "savgol":
                curve_renamed = curve_renamed.apply_savgol_filter(
                    window_length=filter_params["window"],
                    polyorder=filter_params["order"],
                )

        comparison_curves.append(curve_renamed)

    # --- 6. Results tabs ---
    tabs = st.tabs(["📉 Overlay Plot", "📊 Statistics", "🧮 RMSE Matrix"])

    with tabs[0]:
        st.subheader(f"Overlaid '{selected_curve_name}' Profiles")
        units = comparison_curves[0].units or "—"
        # Map units to proper Y-axis labels
        YLABEL_MAP = {
            "N": "Force [N]",
            "N·m": "Moments [Nm]",
            "Nm": "Moments [Nm]",
            "N*m": "Moments [Nm]",
            "m^2": "CdS [m²]",
            "m/s": "Velocity [m/s]",
            "m/s^2": "Acceleration [m/s²]",
            "G": "Acceleration [G]",
            "dimensionless": "Dimensionless [-]",
        }
        ylabel = YLABEL_MAP.get(units, f"{selected_curve_name} [{units}]")
        fig = plot_curves_plotly(
            comparison_curves,
            title=f"Comparison: {selected_curve_name}",
            ylabel=ylabel,
            **plot_style,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.subheader("Statistical Benchmarking")
        labels = [c.name for c in comparison_curves]
        df_stats = compare_statistics(comparison_curves, labels=labels)
        st.dataframe(df_stats, use_container_width=True)

    with tabs[2]:
        st.subheader("RMSE Matrix")
        st.caption(
            "Root Mean Square Error between each pair of simulations. "
            "Curves are first interpolated onto a common time base before comparison."
        )

        aligned = align_curves(comparison_curves)
        n = len(aligned)

        rmse_rows = []
        for i in range(n):
            row = {"Simulation": aligned[i].name}
            for j in range(n):
                if i == j:
                    row[aligned[j].name] = 0.0
                else:
                    row[aligned[j].name] = round(calculate_rmse(aligned[i], aligned[j]), 4)
            rmse_rows.append(row)

        df_rmse = pd.DataFrame(rmse_rows).set_index("Simulation")
        st.dataframe(df_rmse, use_container_width=True)

        st.info("💡 Lower RMSE = simulations are more similar for this property.")
