# DynaProcessing

**DynaProcessing** is a Python-based analysis library designed specifically for Mechanical Engineers to extract, filter, post-process, and visualize data from LS-DYNA parachute FSI simulations.

It provides both a low-level `Curve`-based API for fine-grained control and a high-level declarative `Job` interface for rapid processing.

---

## Key Features

* **Immutable `Curve` Model:** The fundamental data unit — an immutable time-series container that tracks all transformations via `filter_history`. All operations return new Curves; originals are never mutated.
* **Automatic Type Inference:** Pass a directory and the library determines whether to run an Infinite Mass (`.dat` files) or Finite Mass (`.csv` files) pipeline.
* **Digital Signal Processing:** SAE CFC filters, Butterworth low-pass, Moving Average, and Savitzky-Golay filters — all with full traceability.
* **Aerodynamic Calculations:** Drag coefficient (Cd), drag area (CdS) from constant or time-varying velocity, G-force conversion, force derivation (F = m * a).
* **Statistical Analysis:** Mean, std, min, max, RMS, median, peak detection, settling time, FFT frequency analysis, windowed statistics.
* **Event Detection:** Automatic detection of deployment, inflation phases, steady-state, and oscillation characteristics from force/acceleration curves.
* **Simulation Comparison:** Time-series alignment to common grids, RMSE calculation, difference curves, side-by-side statistics.
* **Derivatives:** First and second order numerical derivatives with optional smoothing.
* **Visualization:** Matplotlib (static/PDF) and Plotly (interactive/web) plotting from lists of Curves.
* **Declarative `Job` Interface:** Define a configuration object with directory, variables, filters, and transformations — the library executes the full pipeline.

---

## Installation

Install in editable mode from the monorepo root:
```bash
pip install -e ./libs/dynaprocessing
```

---

## Quick Start

### Using the Curve API directly

```python
from dynaprocessing import InfiniteMassSimulation

# Load a wind-tunnel simulation from a directory of .dat files
sim = InfiniteMassSimulation(directory_path="path/to/results/")

# Access force curves
fpz = sim.curves["Fpz"]

# Apply SAE CFC-60 filter
fpz_filtered = fpz.apply_cfc_filter(cfc=60)

# Get statistics
stats = fpz_filtered.statistics()  # {mean, std, min, max, rms, median}

# Calculate drag coefficient
cd = fpz_filtered.calculate_drag_coefficient(velocity=6.0, area=7.0, rho=1.225)
```

### Using the Job API

```python
from dynaprocessing import Job

job = Job(
    directory="path/to/results/",
    variables=["z_acceleration", "resultant_velocity"],
    to_G=True,
    filter_type="cfc",
    filter_settings=60,
)

curves = job.process()
```

### Finite Mass (Drop Test) Analysis

```python
from dynaprocessing import FiniteMassSimulation

sim = FiniteMassSimulation(directory_path="path/to/drop_test/")

# Get acceleration curve for a node
accel = sim.curves[node_id]["z_acceleration"]

# Convert to G-forces
accel_g = accel.to_g()

# Derive force from acceleration
force = accel.to_force(mass=6.0)
```

---

## Project Structure

```
libs/dynaprocessing/
├── pyproject.toml
├── README.md
├── src/dynaprocessing/
│   ├── __init__.py              # Public API exports
│   ├── models/
│   │   ├── curve.py             # Immutable Curve container
│   │   ├── simulation.py        # Base simulation class
│   │   ├── infinite_mass.py     # Wind-tunnel (.dat) analysis
│   │   └── finite_mass.py       # Drop test (.csv) analysis
│   ├── io/
│   │   ├── lsdyna_csv.py        # .dat and .csv parsers
│   │   └── metadata.py          # Directory name metadata extraction
│   ├── analysis/
│   │   ├── filters.py           # CFC, Butterworth, Moving Avg, Savgol
│   │   ├── statistics.py        # Stats, peaks, settling, FFT
│   │   ├── event_detection.py   # Deploy, inflate, steady-state detection
│   │   ├── derivatives.py       # 1st/2nd order derivatives
│   │   ├── comparison.py        # Align, RMSE, difference curves
│   │   └── postprocess.py       # Declarative Job API
│   └── viz/
│       └── plot_utils.py        # Matplotlib and Plotly plotting
└── tests/                       # 100+ automated tests
    ├── test_curve.py
    ├── test_filters.py
    ├── test_parsers.py
    ├── test_statistics.py
    ├── test_event_detection.py
    ├── test_derivatives.py
    ├── test_comparison.py
    ├── test_physics.py
    └── test_metadata.py
```
