"""aerocfd module — slice 1: single page, no database.

User enters Aircraft references, OC, and a small α-case table. Click "Plot"
to see CL–α, CD–α, L/D–α, CL–CD, Cm–α derived from raw body-frame loads.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from aerocfd import (
    AeroDataset, Aircraft, AlphaCase, ConvergenceStatus, OperatingCondition,
)
from aerocfd.viz.plot_utils import (
    cd_alpha_figure, cl_alpha_figure, cm_alpha_figure,
    drag_polar_figure, lift_to_drag_alpha_figure,
)


def render():
    st.title("aerocfd — Aircraft polar from raw Fluent loads")
    st.caption("Slice 1: in-memory only. Refreshing the page resets everything.")

    # ---- Aircraft section ----
    st.header("Aircraft")
    ac_col_a, ac_col_b, ac_col_c, ac_col_d = st.columns(4)
    ac_name = ac_col_a.text_input("Name", value="Reference")
    s_ref = ac_col_b.number_input("S_ref [m²]", min_value=0.0, value=10.0, step=0.1, format="%.4f")
    c_ref = ac_col_c.number_input("c_ref [m]", min_value=0.0, value=1.5, step=0.01, format="%.4f")
    b_ref = ac_col_d.number_input("b_ref [m]", min_value=0.0, value=8.0, step=0.1, format="%.4f")

    # ---- Operating condition section ----
    st.header("Operating condition")
    oc_col_a, oc_col_b, oc_col_c = st.columns(3)
    oc_name = oc_col_a.text_input("OC name", value="SL_50mps")
    velocity = oc_col_b.number_input("Velocity [m/s]", min_value=0.0, value=50.0, step=1.0)
    density = oc_col_c.number_input("Density [kg/m³]", min_value=0.0, value=1.225, step=0.001, format="%.4f")

    # ---- Alpha-cases table (body-frame totals; Fx is forward-positive, so a
    #      draggy body has negative Fx — the library turns that into positive drag) ----
    st.header("Alpha cases (body-frame totals)")
    default_rows = pd.DataFrame({
        "alpha_deg": [-5.0, 0.0, 5.0, 10.0, 15.0],
        "fx_n":      [-12.0, -10.0, -15.0, -30.0, -55.0],
        "fz_n":      [-300.0, 200.0, 700.0, 1200.0, 1600.0],
        "my_nm":     [-25.0, 0.0, 25.0, 50.0, 75.0],
        "convergence_status": [ConvergenceStatus.UNKNOWN.value] * 5,
    })
    status_options = [s.value for s in ConvergenceStatus]
    edited = st.data_editor(
        default_rows,
        num_rows="dynamic",
        column_config={
            "alpha_deg": st.column_config.NumberColumn("α [deg]", format="%.2f"),
            "fx_n": st.column_config.NumberColumn("Fx [N]", help="Body x, forward-positive; drag is -X so a draggy body has Fx<0", format="%.3f"),
            "fz_n": st.column_config.NumberColumn("Fz [N]", format="%.3f"),
            "my_nm": st.column_config.NumberColumn("My [N·m]", help="Raw Fluent My (sign-flipped in library)", format="%.3f"),
            "convergence_status": st.column_config.SelectboxColumn("Convergence", options=status_options),
        },
        use_container_width=True,
    )

    # ---- Plot button ----
    if st.button("Plot", type="primary"):
        aircraft = Aircraft(name=ac_name, s_ref_m2=s_ref, c_ref_m=c_ref, b_ref_m=b_ref)
        oc = OperatingCondition(name=oc_name, velocity_mps=velocity, density_kgpm3=density)
        cases = []
        for _, row in edited.iterrows():
            if pd.isna(row["alpha_deg"]):
                continue
            cases.append(AlphaCase(
                alpha_deg=float(row["alpha_deg"]),
                fx_n=float(row["fx_n"]),
                fz_n=float(row["fz_n"]),
                my_nm=float(row["my_nm"]),
                convergence_status=ConvergenceStatus(row["convergence_status"]),
            ))

        if len(cases) < 2:
            st.error("Need at least 2 α cases to plot a polar.")
        else:
            dataset = AeroDataset(aircraft=aircraft, operating_condition=oc, alpha_cases=cases)
            st.success(f"Built dataset with {len(cases)} cases. q∞ = {dataset.dynamic_pressure_pa:.2f} Pa.")

            cd_polar = dataset.cd()
            # Runtime echo of gold test #4: a negative CD signals a bad input
            # convention (wrong Fx sign). Non-blocking warning, per design §7.6.
            if np.any(cd_polar.values < 0):
                st.warning(
                    "Some CD values are negative. For a normal draggy body CD should be "
                    "positive — check that Fx follows the convention (forward-positive, "
                    "drag = -X). This usually means the input sign convention is off."
                )

            # Lift, drag, and moment coefficient curves — three tall (1:2) plots side by side.
            lift_col, drag_col, moment_col = st.columns(3)
            lift_col.plotly_chart(cl_alpha_figure(dataset.cl()), width="content")
            drag_col.plotly_chart(cd_alpha_figure(cd_polar), width="content")
            moment_col.plotly_chart(cm_alpha_figure(dataset.cm()), width="content")

            # Efficiency and the aerodynamic (drag) polar — square (1:1) plots.
            efficiency_col, polar_col = st.columns(2)
            efficiency_col.plotly_chart(lift_to_drag_alpha_figure(dataset.lift_to_drag()), width="content")
            polar_col.plotly_chart(drag_polar_figure(dataset.cl(), cd_polar), width="content")
