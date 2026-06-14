"""Seed a demo aircraft into the aerocfd database for testing.

Creates one aircraft ("Demo — Ellipse") with parts grouped into Wing / Fuselage /
Tail, one operating condition, and an α sweep. Per part and α it writes raw
body-frame loads (Fx, Fz) and a pitching moment at each of the three reference
points (20/25/30% MAC). The per-reference moments are produced by transferring a
base moment along the chord, so they vary realistically like a real CFD sheet.

Run it (re-running replaces the demo aircraft cleanly):

    /home/kaspar/Projects/PhD/AerisVault/.venv/bin/python \
        apps/aerisvault/scripts/seed_aerocfd_demo.py

Then open the portal → Aircraft CFD → the demo aircraft is ready to explore.
"""
from __future__ import annotations

from aerocfd.analysis.coefficients import dynamic_pressure

from aerisvault.modules.aerocfd.core.bootstrap import DB_NAME
from aerisvault.modules.aerocfd.core.database import AeroCfdDatabase
from aerisvault.shared.paths import data_dir_for

AIRCRAFT_NAME = "Demo — Ellipse"

# Reference geometry (SI).
S_REF_M2 = 10.0
C_REF_M = 1.5
B_REF_M = 8.0
VELOCITY_MPS = 50.0
DENSITY_KGPM3 = 1.225

ALPHA_SWEEP_DEG = [-5.0, 0.0, 5.0, 10.0, 15.0]

# Reference points (% MAC) and the base point the entered moment is about.
REFERENCE_POINTS = {"20% MAC": 0.20, "25% MAC": 0.25, "30% MAC": 0.30}
BASE_REFERENCE = "20% MAC"

# Per-part model: group, and simple body-frame coefficient build-up.
#   cz0, cza : normal-force coeff at α=0 and its per-degree slope (drives Fz/lift)
#   cd0, cdk : axial drag coeff at α=0 and a quadratic-in-α term (drives Fx, always a -X force)
#   cm0, cma : Fluent pitching-moment coeff at the BASE reference, α=0 and slope
#              (positive Fluent slope → stabilising once the library flips the sign)
PARTS = {
    # name        group        cz0     cza      cd0     cdk     cm0      cma
    "wing":      ("Wing",     0.150,  0.0110,  0.0080, 0.020, -0.010,  0.0010),
    "slot":      ("Wing",     0.010,  0.0015,  0.0010, 0.002, -0.001,  0.0002),
    "wing-te":   ("Wing",     0.000,  0.0002,  0.0002, 0.001,  0.000,  0.00005),
    "fuselage":  ("Fuselage", -0.010, 0.0005,  0.0020, 0.003,  0.004,  0.0003),
    "canopy":    ("Fuselage", 0.005,  0.0003,  0.0005, 0.001,  0.002,  0.0001),
    "engine":    ("Fuselage", 0.002,  0.0002,  0.0010, 0.001, -0.003,  0.0001),
    "tail":      ("Tail",     0.001,  0.0001,  0.0010, 0.001,  0.002,  0.0010),
    "vop":       ("Tail",    -0.002,  0.0020,  0.0007, 0.001, -0.020,  0.0060),
}

Q_PA = dynamic_pressure(DENSITY_KGPM3, VELOCITY_MPS)


def _part_loads_at(alpha_deg: float, part_ids: dict, ref_ids: dict) -> list[dict]:
    """Build the per-part load entries for one α (forces + moments per reference)."""
    entries = []
    for name, (_group, cz0, cza, cd0, cdk, cm0, cma) in PARTS.items():
        fz_n = (cz0 + cza * alpha_deg) * Q_PA * S_REF_M2
        # Drag is a -X force; it grows with α². (alpha/10) keeps the quadratic gentle.
        cd = cd0 + cdk * (alpha_deg / 10.0) ** 2
        fx_n = -cd * Q_PA * S_REF_M2
        my_base_nm = (cm0 + cma * alpha_deg) * Q_PA * S_REF_M2 * C_REF_M

        # Transfer the base moment to each reference point along the chord:
        # moving the reference aft by Δx changes the pitching moment by -Fz·Δx.
        moments = {}
        for label, position in REFERENCE_POINTS.items():
            delta_x_m = (position - REFERENCE_POINTS[BASE_REFERENCE]) * C_REF_M
            moments[ref_ids[label]] = my_base_nm - fz_n * delta_x_m

        entries.append({
            "part_id": part_ids[name],
            "fx_n": fx_n,
            "fz_n": fz_n,
            "moments": moments,
        })
    return entries


def main() -> None:
    db = AeroCfdDatabase(f"sqlite:///{data_dir_for('aerocfd') / DB_NAME}")

    # Replace any previous demo aircraft so re-running gives a clean seed.
    for existing in db.list_aircraft():
        if existing.name == AIRCRAFT_NAME:
            db.delete_aircraft(existing.id)

    aircraft = db.create_aircraft(
        name=AIRCRAFT_NAME, s_ref_m2=S_REF_M2, c_ref_m=C_REF_M, b_ref_m=B_REF_M,
        description="Synthetic test aircraft (Ellipse-style parts) for exercising the aerocfd module.",
    )
    part_ids = {name: db.add_part(aircraft.id, name, group).id for name, (group, *_) in PARTS.items()}
    ref_ids = {ref.label: ref.id for ref in db.list_reference_points(aircraft.id)}

    oc = db.create_operating_condition(
        aircraft.id, name="SL_50mps", velocity_mps=VELOCITY_MPS, density_kgpm3=DENSITY_KGPM3,
        description="Sea-level, 50 m/s.",
    )
    for alpha in ALPHA_SWEEP_DEG:
        db.set_alpha_case(oc.id, alpha, _part_loads_at(alpha, part_ids, ref_ids),
                          convergence_status="converged")

    print(f"Seeded '{AIRCRAFT_NAME}': {len(PARTS)} parts in 3 groups, "
          f"{len(db.list_reference_points(aircraft.id))} reference points, "
          f"1 operating condition, {len(ALPHA_SWEEP_DEG)} α cases.")
    print(f"Database: {data_dir_for('aerocfd') / DB_NAME}")


if __name__ == "__main__":
    main()
