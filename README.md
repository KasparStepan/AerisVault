# 🚀 AerisVault Workspace

> **Notice:** The architecture, directory structure, and initial documentation of this project were drafted with the assistance of AI.

## Overview
Welcome to the **AerisVault Workspace**. This repository is a Monorepo containing a complete Simulation Process and Data Management (SPDM) ecosystem designed for Fluid-Structure Interaction (FSI) simulations of parachutes in LS-Dyna.

Instead of a monolithic script, this workspace strictly separates the "dumb" user interfaces from the "smart" engineering solvers and generators.

## 🏗️ Ecosystem Architecture

The repository is divided into two main categories: **Applications** (frontends that users interact with) and **Libraries** (computational engines that do the heavy lifting).

### Applications (`apps/`)
* **[`aerisvault-ui`](apps/aerisvault-ui/)**: The main web portal built with Streamlit. It provides a user-friendly interface to configure drop tests, generate simulation inputs, and visualize 3D kinematics and data without writing code.

### Libraries (`libs/`)
* **[`dynaprep`](libs/dynaprep/)**: The Pre-processor. A lightweight templating engine (powered by Jinja2) that safely generates LS-Dyna input decks (`.k` files) from static meshes and dynamic boundary conditions.
* **[`dynaprocessing`](libs/dynaprocessing/)**: The Post-processor. A heavy computational library used to parse raw LS-Dyna outputs (`nodout`, `d3plot`), apply digital signal filters (e.g., SAE, CFC), and extract lightweight `.parquet` files for fast visualization.

## 📚 Documentation
Detailed documentation for the architecture, development guidelines, and deployment strategies can be found in the `docs/` directory:
* [Architecture Overview](docs/architecture.md)
* [Development & Contribution Guide](docs/development.md)
* [Getting Started / Installation](docs/getting_started.md)

*(Note: Library-specific examples and Jupyter Notebooks are located within their respective `examples/` folders inside `libs/`.)*

## 🚀 Quick Start (Development)
To set up the workspace locally for development:

1. Clone the repository.
2. Ensure you have Python 3.10+ installed.
3. Install the local libraries and app dependencies in editable mode:
   ```bash
   pip install -e ./libs/dynaprep
   pip install -e ./libs/dynaprocessing
   pip install -r ./apps/aerisvault-ui/requirements.txt
   ```
4. Run the UI:
   ```bash
   cd apps/aerisvault-ui
   streamlit run src/aerisvault/app.py
   ```