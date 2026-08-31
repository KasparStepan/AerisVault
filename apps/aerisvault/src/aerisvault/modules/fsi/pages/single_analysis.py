"""
AerisVault UI - Single Simulation Analysis
Post-processing and visualization using dynaprocessing library.
"""

import streamlit as st
import pandas as pd
from dynaprocessing.models.infinite_mass import InfiniteMassSimulation
from dynaprocessing.models.finite_mass import FiniteMassSimulation
from dynaprocessing.viz.plot_utils import plot_curves_plotly
from dynaprocessing.analysis.event_detection import auto_detect_events
from aerisvault.modules.fsi.ui.components import sidebar_filter_settings, sidebar_plot_style, simulation_selector
from aerisvault.modules.fsi.core.bootstrap import ensure_initialized


def render():
    ensure_initialized()
    db = st.session_state["fsi.db"]
    storage = st.session_state["fsi.storage"]

    st.title("📊 Single Simulation Analysis")

    # --- 1. Select simulation ---
    selected_sim = simulation_selector()

    if not selected_sim:
        st.stop()

    st.sidebar.markdown("---")
    st.sidebar.write(f"**Loaded:** {selected_sim.name}")
    st.sidebar.write(f"**Type:** {selected_sim.analysis_type.replace('_', ' ').title()}")

    # --- 2. Sidebar filter controls ---
    filter_params = sidebar_filter_settings()

    # --- 3. Load curves from disk ---
    files = db.get_files_by_simulation(selected_sim.id)
    drag_files = [f for f in files if f.file_type.value == "drag_result"]

    if not drag_files:
        st.warning("No result files attached to this simulation. Go to the Database page to upload files.")
        st.stop()

    st.write(f"Analysing: `{drag_files[0].original_filename}`")

    sim_dir = storage.base_dir / "raw" / f"sim_{selected_sim.id}"

    # curves_dict stores {name: Curve} for easy lookup when computing derived quantities
    curves_dict: dict = {}

    try:
        if selected_sim.analysis_type == "infinite_mass":
            # InfiniteMassSimulation reads .dat files → curves is Dict[str, Curve]
            sim_model = InfiniteMassSimulation(directory_path=sim_dir)
            curves_dict = dict(sim_model.curves)

        else:
            # FiniteMassSimulation reads .csv files → curves is Dict[node_id, Dict[str, Curve]]
            # Flatten to {curve_name: Curve}, keeping first match per name
            sim_model = FiniteMassSimulation(directory_path=sim_dir)
            for node_curves in sim_model.curves.values():
                for name, curve in node_curves.items():
                    if name not in curves_dict:
                        curves_dict[name] = curve

    except FileNotFoundError:
        st.error(f"Simulation directory not found: `{sim_dir}`")
        st.stop()

    if not curves_dict:
        st.error("No curves could be loaded from the result files. Check that the files are in the correct format.")
        st.stop()

    # --- 4. Sidebar: derived quantities ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📐 Derived Quantities")

    compute_force = False
    compute_cds = False

    if selected_sim.analysis_type == "finite_mass":
        # For finite mass: we can compute F = m·a and CdS = 2F / (ρ·v²(t))
        has_accel = any("acceleration" in name for name in curves_dict)
        has_velocity = any("velocity" in name for name in curves_dict)

        if has_accel and selected_sim.mass and selected_sim.mass > 0:
            compute_force = st.sidebar.checkbox(
                "Resultant force (F = m × a)",
                value=False,
                help=f"Computes aerodynamic force from acceleration × mass ({selected_sim.mass} kg).",
            )
        elif has_accel:
            st.sidebar.caption("Set mass on the Database page to enable force computation.")

        if has_velocity:
            compute_cds = st.sidebar.checkbox(
                "Drag area CdS = 2F / (ρ·v²)",
                value=False,
                disabled=not (compute_force or any("force" in n for n in curves_dict)),
                help="Requires either a force curve or force computation enabled above.",
            )
        if not has_velocity and not has_accel:
            st.sidebar.caption("No acceleration or velocity curves found for derived quantities.")

    else:
        # For infinite mass: resultant force and CdS are always computed when possible
        has_force = any(name.startswith("Fp") for name in curves_dict)
        has_all_force_components = all(
            name in curves_dict for name in ("Fpx", "Fpy", "Fpz")
        )

        # Resultant force is always computed when all 3 components are available
        compute_resultant = has_all_force_components

        # CdS is always computed when force curves and velocity are available
        if has_force and selected_sim.velocity and selected_sim.velocity > 0:
            compute_cds = True
        elif has_force:
            st.sidebar.caption("Set velocity on the Database page to enable CdS.")

    # --- Figure settings (bottom of sidebar) ---
    plot_style = sidebar_plot_style()

    # --- 5. Apply filters ---
    processed_curves = []
    for curve in curves_dict.values():
        if not filter_params["enabled"]:
            processed_curves.append(curve)
            continue

        filter_type = filter_params["type"]
        if filter_type == "cfc":
            processed_curves.append(curve.apply_cfc_filter(cfc=filter_params["cfc"]))
        elif filter_type == "butterworth":
            processed_curves.append(curve.apply_butterworth_filter(cutoff_freq=filter_params["cutoff"]))
        elif filter_type == "moving_average":
            processed_curves.append(curve.apply_moving_average_filter(window_size=filter_params["window"]))
        elif filter_type == "savgol":
            processed_curves.append(curve.apply_savgol_filter(
                window_length=filter_params["window"],
                polyorder=filter_params["order"],
            ))

    # Rebuild the dict from filtered curves for easy lookup
    filtered_dict = {c.name: c for c in processed_curves}

    # --- 6. Compute derived quantities and append to the list ---
    derived_curves = []

    if compute_force and selected_sim.analysis_type == "finite_mass":
        # Find acceleration curves, compute F = m·a for each
        for curve in processed_curves:
            if "acceleration" in curve.name:
                force_curve = curve.to_force(mass=selected_sim.mass)
                derived_curves.append(force_curve)
                filtered_dict[force_curve.name] = force_curve

    if selected_sim.analysis_type == "infinite_mass" and compute_resultant:
        fpx = filtered_dict.get("Fpx")
        fpy = filtered_dict.get("Fpy")
        fpz = filtered_dict.get("Fpz")
        if fpx and fpy and fpz:
            from dynaprocessing.models.curve import Curve as _Curve
            resultant_curve = _Curve.resultant(fpx, fpy, fpz)
            derived_curves.append(resultant_curve)
            filtered_dict[resultant_curve.name] = resultant_curve

    if compute_cds:
        if selected_sim.analysis_type == "finite_mass":
            # CdS with time-varying velocity: CdS = 2F / (ρ·v²(t))
            # Find the velocity curve (prefer resultant_velocity)
            velocity_curve = (
                filtered_dict.get("resultant_velocity")
                or next((c for c in processed_curves if "velocity" in c.name), None)
            )
            if velocity_curve:
                for curve in list(derived_curves) + processed_curves:
                    if curve.units == "N" or "force" in curve.name:
                        cds_curve = curve.calculate_cds_from_velocity(
                            velocity_curve, rho=selected_sim.air_density
                        )
                        derived_curves.append(cds_curve)
        else:
            # Infinite mass: CdS with constant velocity
            # Include both individual force components and resultant force
            force_curves = [c for c in processed_curves if c.name.startswith("Fp")]
            if "resultant_force" in filtered_dict:
                force_curves.append(filtered_dict["resultant_force"])
            for curve in force_curves:
                cds_curve = curve.calculate_cds(
                    v=selected_sim.velocity, rho=selected_sim.air_density
                )
                derived_curves.append(cds_curve)

    # Merge all curves for display
    all_curves = processed_curves + derived_curves


    # --- 7. Dashboard tabs ---
    tabs = st.tabs(["📈 Plots", "📋 Statistics", "⚡ Peak Load", "🎯 Events", "🗂️ Raw Data"])

    with tabs[0]:
        st.subheader("Interactive Plots")

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

        # Group curves by unit
        unit_groups: dict = {}
        for curve in all_curves:
            unit_label = curve.units or "dimensionless"
            unit_groups.setdefault(unit_label, []).append(curve)

        # Fixed display order: Force, CdS, Moments, then everything else
        UNIT_ORDER = ["N", "m^2", "N·m", "Nm", "N*m"]
        ordered_units = [u for u in UNIT_ORDER if u in unit_groups]
        remaining_units = [u for u in unit_groups if u not in UNIT_ORDER]
        ordered_units.extend(remaining_units)

        for unit_label in ordered_units:
            group = unit_groups[unit_label]
            ylabel = YLABEL_MAP.get(unit_label, f"{unit_label}")
            fig = plot_curves_plotly(group, title=ylabel, ylabel=ylabel, **plot_style)
            st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.subheader("Summary Statistics")
        stats_rows = []
        for curve in all_curves:
            row = curve.statistics()
            row["Curve"] = curve.name
            row["Units"] = curve.units or "—"
            stats_rows.append(row)

        df_stats = pd.DataFrame(stats_rows).set_index("Curve")
        st.dataframe(df_stats, use_container_width=True)

        # Drag coefficient (Cd) — only for infinite mass with velocity + area
        if selected_sim.analysis_type == "infinite_mass" and selected_sim.velocity and selected_sim.ref_area:
            st.divider()
            st.subheader("Drag Coefficient (Cd)")
            st.caption(
                f"Cd = 2·Fpz / (ρ·v²·A)  |  "
                f"v = {selected_sim.velocity} m/s, A = {selected_sim.ref_area} m², "
                f"ρ = {selected_sim.air_density} kg/m³"
            )

            fpz_curve = next((c for c in processed_curves if "Fpz" in c.name), None)
            if fpz_curve:
                cd_curve = fpz_curve.calculate_drag_coefficient(
                    v=selected_sim.velocity,
                    A=selected_sim.ref_area,
                    rho=selected_sim.air_density,
                )
                st.plotly_chart(
                    plot_curves_plotly([cd_curve], title="Drag Coefficient Cd over time", **plot_style),
                    use_container_width=True,
                )
                cd_stats = cd_curve.statistics()
                col1, col2, col3 = st.columns(3)
                col1.metric("Mean Cd", f"{cd_stats['mean']:.4f}")
                col2.metric("Max Cd", f"{cd_stats['max']:.4f}")
                col3.metric("Std Dev", f"{cd_stats['std']:.4f}")
            else:
                st.info("Drag coefficient requires an 'Fpz' (axial force) curve.")

    with tabs[2]:
        st.subheader("⚡ Peak / Snatch Load")
        st.caption(
            "Raw špička je jediný vzorek near-singulárního rázu — je řízená sítí a časovým krokem. "
            "CFC filtr (SAE J211) odstraní gridem řízený vysokofrekvenční obsah a dá fyzikálně "
            "srovnatelnou špičku. Vždy se zobrazí obojí: raw i filtrovaná."
        )

        # Silové křivky bereme ze surových (nefiltrovaných) dat — nezávisle na
        # postranním filtru zobrazení. Snatch load nás zajímá na Fpz (osová),
        # volitelně na výslednici všech tří složek.
        force_curves = {name: c for name, c in curves_dict.items() if c.units == "N"}
        if all(component in curves_dict for component in ("Fpx", "Fpy", "Fpz")):
            from dynaprocessing.models.curve import Curve as _Curve
            resultant_raw = _Curve.resultant(
                curves_dict["Fpx"], curves_dict["Fpy"], curves_dict["Fpz"]
            )
            force_curves[resultant_raw.name] = resultant_raw

        if not force_curves:
            st.info("Nenalezena žádná silová křivka (jednotka N) pro analýzu špičky.")
        else:
            col_curve, col_cfc = st.columns(2)
            default_index = list(force_curves).index("Fpz") if "Fpz" in force_curves else 0
            selected_force = col_curve.selectbox(
                "Silová křivka", list(force_curves), index=default_index
            )
            cfc_class = col_cfc.selectbox(
                "CFC třída (SAE J211)", [60, 180, 600, 1000], index=0,
                format_func=lambda c: f"CFC{c}  (≈ {int(c * 1.65)} Hz)",
            )

            raw_curve = force_curves[selected_force]
            filtered_curve = raw_curve.apply_cfc_filter(cfc=cfc_class)

            # Dominantní špička = extrém s největší velikostí (u Fpz je to min).
            def dominant_peak(curve):
                min_value, time_at_min = curve.get_min()
                max_value, time_at_max = curve.get_max()
                if abs(min_value) >= abs(max_value):
                    return min_value, time_at_min
                return max_value, time_at_max

            raw_peak, raw_peak_time = dominant_peak(raw_curve)
            filtered_peak, filtered_peak_time = dominant_peak(filtered_curve)
            reduction_percent = (
                (abs(raw_peak) - abs(filtered_peak)) / abs(raw_peak) * 100
                if raw_peak else 0.0
            )

            # SAE J211 doporučuje vzorkování ≥ 10× CFC třída; při nižším filtr ořezává fyziku.
            sampling_hz = (len(raw_curve.time) - 1) / (raw_curve.time[-1] - raw_curve.time[0])
            if sampling_hz < 10 * cfc_class:
                st.warning(
                    f"Vzorkování dat ~{sampling_hz:.0f} Hz je pod SAE doporučením "
                    f"(≥ {10 * cfc_class} Hz pro CFC{cfc_class}). Zvol nižší CFC třídu, "
                    f"nebo v simulaci zvyš výstupní frekvenci drag databáze."
                )

            col_raw, col_filt, col_red = st.columns(3)
            col_raw.metric("RAW špička", f"{raw_peak:.1f} N", help=f"v čase t = {raw_peak_time:.4f} s")
            col_filt.metric(f"CFC{cfc_class} špička", f"{filtered_peak:.1f} N", help=f"v čase t = {filtered_peak_time:.4f} s")
            col_red.metric("Snížení filtrem", f"{reduction_percent:.0f} %", help="o kolik CFC filtr snížil velikost špičky")

            st.plotly_chart(
                plot_curves_plotly(
                    [raw_curve, filtered_curve],
                    title=f"{selected_force}: raw vs CFC{cfc_class}",
                    ylabel="Force [N]",
                    **plot_style,
                ),
                use_container_width=True,
            )
            st.caption(
                "Pozn.: pro spolehlivé porovnání špiček mezi sítěmi je nutná stejná CFC třída "
                "a dostatek replikátů (nafukovací ráz je chaotický)."
            )

    with tabs[3]:
        st.subheader("Event Detection")
        st.caption("Automatically identifies key phases in the parachute deployment sequence.")

        fpz_curve = next((c for c in processed_curves if "Fpz" in c.name), None)
        if fpz_curve:
            events = auto_detect_events(fpz_curve)

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Deployment**")
                deploy = events["deployment"]
                if deploy["detected"]:
                    st.success(f"Detected at t = {deploy['deployment_time']:.3f} s")
                    st.write(f"Deployment force: {deploy['deployment_force']:.1f} N")
                else:
                    st.info("No deployment event detected.")

                st.write("**Inflation Phase**")
                inf = events["inflation"]
                st.write(f"Peak force: {inf['peak_force']:.1f} N")
                st.write(f"Inflation duration: {inf['inflation_duration']:.3f} s")

            with col2:
                st.write("**Steady State**")
                steady = events["steady_state"]
                if steady["detected"]:
                    st.success(f"Reached at t = {steady['steady_time']:.3f} s")
                    st.write(f"Settled force: {steady['steady_value']:.1f} N")
                else:
                    st.warning("Steady state not detected in this time window.")

                st.write("**Oscillations**")
                osc = events["oscillations"]
                if osc["oscillating"]:
                    st.warning(f"Oscillating at {osc['dominant_frequency']:.2f} Hz")
                    st.write(f"Amplitude: {osc['amplitude']:.1f} N")
                else:
                    st.success("No significant oscillations detected.")
        else:
            st.info(
                "Event detection requires an 'Fpz' force curve. "
                "This is available for infinite mass simulations."
            )

    with tabs[4]:
        st.subheader("Raw Values")
        df_raw = pd.DataFrame({"time [s]": all_curves[0].time})
        for curve in all_curves:
            column_label = f"{curve.name} [{curve.units or '—'}]"
            df_raw[column_label] = curve.values

        st.dataframe(df_raw, use_container_width=True)
        st.download_button(
            "⬇️ Download as CSV",
            df_raw.to_csv(index=False).encode("utf-8"),
            f"{selected_sim.name}_processed.csv",
            "text/csv",
        )
