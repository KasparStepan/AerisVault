"""Shared fixtures for the aerocfd test suite."""
import numpy as np
import pytest


@pytest.fixture
def alpha_grid_deg():
    """Five α values spanning a typical small-angle sweep."""
    return np.array([-5.0, 0.0, 5.0, 10.0, 15.0])


@pytest.fixture
def reference_aircraft_kwargs():
    """Reasonable defaults for a small fixed-wing reference aircraft."""
    return dict(
        name="Reference",
        s_ref_m2=10.0,
        c_ref_m=1.5,
        b_ref_m=8.0,
    )


@pytest.fixture
def reference_operating_condition_kwargs():
    """Sea-level standard atmosphere, 50 m/s."""
    return dict(
        name="SL_50mps",
        velocity_mps=50.0,
        density_kgpm3=1.225,
    )


@pytest.fixture
def stable_airfoil_alpha_cases():
    """Synthetic α sweep that mimics a stable airfoil:
    - lift increases ~linearly with α
    - drag is small and roughly parabolic
    - Fluent My is positive for positive α (nose-DOWN in this convention),
      so after the sign flip Cm should be negative for positive α — the
      hallmark of a longitudinally stable configuration.
    """
    from aerocfd.models.alpha_case import AlphaCase
    cases = []
    for alpha in [-5.0, 0.0, 5.0, 10.0, 15.0]:
        # body-frame totals
        fz = 100.0 * alpha + 200.0       # rough lift slope, body frame
        fx = -10.0 - 0.5 * alpha**2      # small drag (negative = backward)
        my_fluent = 5.0 * alpha          # nose-down positive in this convention
        cases.append(AlphaCase(alpha_deg=alpha, fx_n=fx, fz_n=fz, my_nm=my_fluent))
    return cases
