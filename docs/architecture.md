# AerisVault: System Architecture

> **Notice:** This documentation was initially drafted with the assistance of AI. It serves as the foundational design document for the AerisVault ecosystem.

## 1. Executive Summary
AerisVault is a Simulation Process and Data Management (SPDM) platform tailored for Fluid-Structure Interaction (FSI) simulations of parachutes in LS-DYNA. The primary goal of this architecture is to provide a user-friendly web interface while strictly decoupling the "dumb" user interface from the "smart" engineering computational engines.

## 2. Core Architectural Principles
The project is built as a **Monorepo** using the **`src` layout** pattern. This ensures that:
* **Separation of Concerns:** The User Interface (App) and the solvers (Libraries) are physically and logically separated.
* **Safe Imports:** Libraries cannot import from the UI, preventing circular dependencies.
* **Testability:** The `src` layout enforces proper installation of local packages during testing, mimicking the exact environment of an end-user.

## 3. System Components
The AerisVault ecosystem consists of three primary modules:

### A. AerisVault UI (The Application)
* **Location:** `apps/aerisvault-ui/`
* **Tech Stack:** Streamlit, SQLAlchemy, Plotly.
* **Role:** The frontend portal. It connects to the SQLite metadata database and acts as the orchestrator. Users upload LS-DYNA output files, browse simulations, run analysis, and compare results. All computation is delegated to `dynaprocessing`.

**Pages:**
1. **Dashboard** (`app.py`) — Overview with simulation count and quick navigation.
2. **Database** (`pages/01_database.py`) — Simulation registry, file upload, tagging.
3. **Single Analysis** (`pages/02_single_analysis.py`) — Filter, derive, visualize, and detect events for a single simulation.
4. **Comparison** (`pages/03_comparison.py`) — Multi-simulation overlay, RMSE, side-by-side statistics.
5. **Settings** (`pages/04_settings.py`) — Filter and plot configuration (persisted to `config.json`).

### B. DynaProcessing (The Post-processor)
* **Location:** `libs/dynaprocessing/`
* **Tech Stack:** NumPy, SciPy, Pandas, Matplotlib, Plotly, PyArrow.
* **Role:** The core computational library. It parses raw LS-DYNA output files (`.dat` for infinite mass / wind-tunnel, `.csv` for finite mass / drop test), applies digital signal filtering (SAE CFC, Butterworth, Moving Average, Savitzky-Golay), calculates aerodynamic coefficients, detects events, computes statistics, and produces visualizations.

### C. DynaPrep (The Pre-processor) — Not Yet Implemented
* **Location:** `libs/dynaprep/`
* **Tech Stack:** Python, Jinja2.
* **Role:** (Future) A lightweight library responsible for generating LS-DYNA input decks (`.k` files). Currently an empty stub.

## 4. Directory Structure
```text
AerisVault/
├── config.json             # Application configuration (filter & plot settings)
├── aerisvault.db           # SQLite metadata database
├── data/                   # Simulation data (not in Git)
│   ├── raw/                # Uploaded .dat/.csv files (sim_{id}/)
│   └── processed/          # Converted .parquet files (sim_{id}/)
├── docs/                   # Centralised ecosystem documentation
├── libs/
│   ├── dynaprocessing/     # Post-processor library (implemented, tested)
│   └── dynaprep/           # Pre-processor library (stub)
└── apps/
    ├── aerisvault-ui/      # Streamlit Web Application
    └── aerisvault-old/     # Legacy monolithic app (reference only)
```

## 5. Data Flow (Current Implementation)

1. **Upload:** User uploads raw LS-DYNA output files (`.dat` or `.csv`) via the Database page.
2. **Storage:** Files are saved to `data/raw/sim_{id}/`. Metadata (simulation name, type, parameters) is stored in SQLite via SQLAlchemy ORM.
3. **Conversion:** On upload, `.dat`/`.csv` files are automatically parsed by `dynaprocessing` and converted to `.parquet` format in `data/processed/sim_{id}/` for fast loading.
4. **Analysis:** The Analysis page loads curves via `InfiniteMassSimulation` or `FiniteMassSimulation`, applies user-selected filters, computes derived quantities (G-forces, CdS, derivatives), detects events, and renders interactive Plotly charts.
5. **Comparison:** The Comparison page loads curves from multiple simulations, aligns them to a common time grid, and computes RMSE and side-by-side statistics.
