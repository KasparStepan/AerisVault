# AerisVault: System Architecture

> **Notice:** This documentation was initially drafted with the assistance of AI. It serves as the foundational design document for the AerisVault ecosystem.

## 1. Executive Summary
AerisVault is a Simulation Process and Data Management (SPDM) platform tailored for Fluid-Structure Interaction (FSI) simulations of parachutes in LS-Dyna. The primary goal of this architecture is to provide a user-friendly web interface for 3rd-party users while strictly decoupling the "dumb" user interface from the "smart" engineering computational engines.

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
* **Role:** The frontend portal (App). It handles user authentication, connects to the SQLite metadata database, and acts as the orchestrator. It collects user inputs (e.g., mass, velocity) and delegates the actual work to the underlying libraries.

### B. DynaPrep (The Pre-processor)
* **Location:** `libs/dynaprep/`
* **Tech Stack:** Python, Jinja2.
* **Role:** A lightweight library responsible for generating LS-Dyna input decks (`.k` files). It takes static, physics-free meshes from the database and uses Jinja2 templating to dynamically inject boundary conditions, materials, and control cards based on UI inputs.

### C. DynaProcessing (The Post-processor)
* **Location:** `libs/dynaprocessing/`
* **Tech Stack:** NumPy, Pandas, PyVista, Plotly.
* **Role:** A heavy computational library. It parses raw LS-Dyna outputs (e.g., `nodout`, `d3plot`), applies digital signal filtering (SAE, CFC), and reduces massive 3D topologies into lightweight `.parquet` files for fast web rendering.

## 4. Directory Structure
```text
aerisvault-workspace/
├── data/                   # Local databases, static meshes, and parquet results (Not in Git)
├── docs/                   # Centralized ecosystem documentation
├── libs/
│   ├── dynaprep/           # Input generator library
│   └── dynaprocessing/     # Results analyzer library
└── apps/
    └── aerisvault-ui/      # Streamlit Web Application

```

## 5. Data Flow (Simulation Lifecycle)
* **Input:** User configures a drop test via aerisvault-ui.

* **Pre-processing:** The UI calls dynaprep. dynaprep fetches the raw .k mesh, applies .j2 templates, and generates a ready-to-run simulation folder.

* **Execution:** The solver (LS-Dyna) is triggered (locally or via HPC cluster).

* **Post-processing:** The UI calls dynaprocessing on the result folder. The library extracts time-series data and lightweight 3D kinematics, saving them as .parquet.

* **Visualization: The UI reads the .parquet files and renders interactive Plotly charts and 3D animations.