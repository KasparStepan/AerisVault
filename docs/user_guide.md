# User Guide

## Application Overview

AerisVault UI is a web-based tool for managing and analysing LS-DYNA parachute simulation results. It supports two simulation types:

- **Infinite Mass (Wind-Tunnel / ICFD):** Parachute inflated at constant velocity, forces and moments measured from `.dat` files.
- **Finite Mass (Drop Test / CSD):** Parachute deployed during freefall, acceleration and kinematics measured from `.csv` files.

## Pages

### Dashboard
The landing page shows an overview of your simulation database with a count of stored simulations, quick-access buttons, and a table of recent entries.

### Database (Registry & File Management)
Manage your simulation library:
- **Registry tab:** Browse all simulations, search by name.
- **Add Simulation tab:** Create a new simulation entry, set parameters (type, velocity, reference area, mass), and upload LS-DYNA output files.
- **Tags tab:** Create colour-coded tags and assign them to simulations for organisation.

Uploaded `.dat` and `.csv` files are automatically converted to `.parquet` format for fast loading during analysis.

### Single Analysis
Analyse a single simulation in detail:
1. Select a simulation from the dropdown.
2. Choose which curves to plot (forces, accelerations, velocities, etc.).
3. Apply digital filters from the sidebar:
   - **CFC (SAE J211):** Standard crash/drop-test filter. Set the CFC class (e.g., 60).
   - **Butterworth:** Low-pass filter with configurable cutoff frequency and order.
   - **Moving Average:** Simple rolling window smoothing.
   - **Savitzky-Golay:** Polynomial-based smoothing with configurable window and order.
4. Compute derived quantities:
   - Convert accelerations to G-forces.
   - Calculate force from acceleration (F = m * a) for finite mass simulations.
   - Calculate drag area (CdS) from time-varying velocity.
5. View statistics: mean, standard deviation, min, max, RMS for each curve.
6. Run event detection to identify deployment time, inflation phases, steady-state, and oscillation characteristics.

### Comparison
Compare multiple simulations side by side:
1. Select two or more simulations.
2. Curves are aligned to a common time grid via interpolation.
3. View overlaid plots with different colours per simulation.
4. Compute RMSE between curves to quantify differences.
5. Compare statistics in a summary table.

### Settings
Configure default application behaviour:
- **Filter defaults:** Default filter type, CFC class, Butterworth cutoff, moving average window, Savgol parameters.
- **Plot style:** Theme, dimensions, line width, font size, grid visibility.

Settings are persisted to `config.json` in the project root.

## Data Organisation

Simulation data is stored locally:
- **Raw files:** `data/raw/sim_{id}/` — original uploaded `.dat` / `.csv` files.
- **Processed files:** `data/processed/sim_{id}/` — converted `.parquet` files.
- **Metadata:** `aerisvault.db` — SQLite database with simulation entries, file records, and tags.
