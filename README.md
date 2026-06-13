# AerisVault

> **Notice:** The architecture, directory structure, and initial documentation of this project were drafted with the assistance of AI.

## Overview
Welcome to the **AerisVault Workspace**. This repository is a Monorepo containing a complete Simulation Process and Data Management (SPDM) ecosystem designed for Fluid-Structure Interaction (FSI) simulations of parachutes in LS-DYNA.

Instead of a monolithic script, this workspace strictly separates the "dumb" user interfaces from the "smart" engineering solvers and generators.

## Ecosystem Architecture

The repository is divided into two main categories: **Applications** (frontends that users interact with) and **Libraries** (computational engines that do the heavy lifting).

### Applications (`apps/`)
* **[`aerisvault-ui`](apps/aerisvault-ui/)**: The main web portal built with Streamlit. It provides a user-friendly interface to manage simulation data, upload and organise LS-DYNA output files, run post-processing analysis, compare simulations, and visualize results interactively — all without writing code.

### Libraries (`libs/`)
* **[`dynaprocessing`](libs/dynaprocessing/)**: The Post-processor. A computational library used to parse raw LS-DYNA output files (`.dat` for infinite mass / wind-tunnel simulations, `.csv` for finite mass / drop test simulations), apply digital signal filters (SAE CFC, Butterworth, Savitzky-Golay), perform statistical and event analysis, and produce interactive Plotly visualizations.
* **[`dynaprep`](libs/dynaprep/)**: The Pre-processor (stub, not yet implemented). Will be a lightweight templating engine (powered by Jinja2) that generates LS-DYNA input decks (`.k` files) from static meshes and dynamic boundary conditions.

## Documentation
Architecture and conventions live in [`CLAUDE.md`](CLAUDE.md). Active design specs and implementation plans are in `docs/`:
* [Portal architecture spec](docs/superpowers/specs/2026-06-13-portal-architecture-design.md) — the single-shell, modules-as-tools platform design
* [aerocfd design spec](docs/superpowers/specs/2026-05-10-aerocfd-design.md) and [CFD work package](docs/WorkPackages/CFD.md) — aircraft CFD module
* [Implementation plans](docs/superpowers/plans/) — portal+FSI migration, dynaprocessing refinement, aerocfd slice 1
* [DynaPrep requirements](docs/WIP/requirements_dynaprep.md) — design for the future pre-processor library

## Quick Start (Development)
To set up the workspace locally for development:

1. Clone the repository:
   ```bash
   git clone https://github.com/KasparStepan/AerisVault.git
   cd AerisVault
   ```
2. Create and activate a virtual environment (Python 3.10+):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the local libraries and app in editable mode:
   ```bash
   pip install -e ./libs/dynaprocessing
   pip install -e ./apps/aerisvault-ui
   ```
4. Run the UI:
   ```bash
   cd apps/aerisvault-ui
   streamlit run src/aerisvault/app.py
   ```
