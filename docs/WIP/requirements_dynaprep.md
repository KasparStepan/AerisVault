# 🛠️ DynaPrep: Software Architecture & Feature Specification

## 1. Executive Summary
**DynaPrep** is a lightweight, high-speed Python library designed for the automated pre-processing and generation of LS-DYNA input decks (`.k` files). 

As the foundational setup engine within the AerisVault ecosystem, DynaPrep strictly separates "dumb" geometric mesh data from "smart" physical setups. It utilizes a robust templating engine to dynamically inject user-defined boundary conditions, material properties, and solver controls into simulation files, completely eliminating the need for manual text editing or LS-PrePost manipulation for routine analyses.

## 2. Software Architecture
DynaPrep is built on a modular template-driven architecture, ensuring maximum safety against LS-DYNA's strict formatting rules while remaining extremely lightweight.

### 2.1. Structural Layers
* **`templates/` (The Blueprints):** A directory containing physically pre-configured LS-DYNA keyword templates written in **Jinja2** format (`.k.j2`). These files contain the structural logic of the cards but leave variables (like mass, velocity, or termination time) blank.
* **`generator.py` (The Assembly Engine):** The core module that receives parameters from the parent application, loads the appropriate Jinja2 templates, enforces formatting, and writes the final `.k` files to a designated job directory.
* **`environment.py` (Physical Calculators):** A helper module containing domain-specific engineering logic (e.g., calculating ISA standard atmospheric density and pressure from a given drop altitude) before passing the values to the generator.

### 2.2. Dependencies
Unlike heavy computational libraries, DynaPrep is designed to be minimal to ensure rapid execution and easy deployment:
* **`jinja2`**: The core templating engine for safe text substitution.
* **`os` / `pathlib` / `shutil`**: Standard Python libraries for fast file and directory manipulation.

---

## 3. Core Features & Capabilities (Functional Requirements)

### 3.1. Jinja2 Templating & Strict Formatting
* **Feature:** Safe generation of LS-DYNA keyword cards.
* **Behavior:** LS-DYNA requires strict column formatting (typically 10 or 8 characters per field). DynaPrep utilizes Jinja2 macros and Python string formatting (e.g., `{{ "%10.3f" | format(velocity) }}`) to guarantee that generated numbers never "spill over" into adjacent columns, preventing solver `EOF` or `Format` errors.

### 3.2. Modular Assembly via `*INCLUDE_TRANSFORM`
* **Feature:** Safe assembly of multiple independent meshes (e.g., combining a parachute canopy mesh with a payload mesh).
* **Behavior:** To prevent Node, Element, and Part ID collisions, DynaPrep does not attempt to renumber meshes in Python. Instead, it generates a `main.k` file that intelligently uses LS-DYNA's `*INCLUDE_TRANSFORM` card to apply ID offsets (e.g., +1,000,000) dynamically when the solver initializes.

### 3.3. "Dumb" Mesh Architecture
* **Feature:** Protection of core geometric data.
* **Behavior:** DynaPrep never modifies or writes to the source `*NODE` or `*ELEMENT` files stored in the `meshes_db`. It treats these files as read-only, linking them to the generated setup files. This ensures that the master geometric topology is never accidentally corrupted by a web user.

### 3.4. Atmospheric & Physics Calculators
* **Feature:** Translation of user-friendly inputs into solver-ready physics parameters.
* **Behavior:** If a user inputs "Drop Altitude: 5000 m", the `environment.py` module automatically computes the correct air density ($\rho$), dynamic viscosity ($\mu$), and ambient pressure ($P$) according to the International Standard Atmosphere (ISA) model, and injects these specific values into the `*ICFD_MAT` cards.

### 3.5. Automated Job Directory Packaging
* **Feature:** Creation of self-contained, execution-ready solver directories.
* **Behavior:** Upon calling the generation API, the library creates a unique job folder (e.g., `sim_001/`), copies the required read-only meshes into it, writes the dynamically generated `.k` templates, and prepares a master run file, making the folder immediately ready for local execution or HPC cluster submission.

---

## 4. Non-Functional Requirements (NFRs)

### 4.1. Performance & Speed
* Generating a complete FSI simulation setup (consisting of CSD setup, CFD setup, material cards, and boundary conditions) must take less than **0.5 seconds**. The library must operate strictly on text manipulation without loading heavy 3D mesh arrays into memory.

### 4.2. UI Independence (Headless Execution)
* DynaPrep must remain completely agnostic of the Streamlit UI. It must accept standard Python dictionaries or dataclasses as inputs so it can be triggered by a web backend, a REST API, or an automated batch-optimization script equally well.

### 4.3. Determinism & Traceability
* Given the same input parameters (mesh names, masses, velocities), the generator must produce byte-for-byte identical output decks.
* The generator should insert comment lines (`$ Generated by DynaPrep on [Date]`) at the top of the main `.k` files to ensure traceability of the setup origins.

## 5. Keyword File Architecture & Separation of Concerns

To successfully automate LS-DYNA simulations via a web interface, the traditional monolithic keyword file approach is strictly prohibited. DynaPrep enforces a highly modular file structure that physically separates static geometry from dynamic, user-defined physics. 

### 5.1. The Golden Rule: Never Mix Mesh, Materials, and Parts
A common fatal flaw in manual CAE setups is defining `*PART`, `*MAT`, and `*SECTION` inside the same file as the millions of `*NODE` and `*ELEMENT` cards. If a web user wants to change the canopy material from Nylon to Kevlar, the backend would have to parse and rewrite a massive gigabyte-sized text file just to change one `MID` integer.

**The AerisVault Solution:** We strictly separate these entities into three distinct layers:
1. **Geometry (The Body):** Nodes, Elements, and Sets. (Static)
2. **Properties (The DNA):** Materials and Sections. (Dynamic)
3. **Parts (The Bridge):** The `*PART` card itself, which acts purely as a relational link binding a Geometry Set to a Property. (Dynamic)

### 5.2. Full Execution Directory Structure
When `dynaprep` generates a simulation, the final execution directory (e.g., `sim_run_001/`) will look exactly like this:

```text
sim_run_001/
├── main_run.k                     <-- Master execution file (Router)
│
├── 01_geometry/                   <-- (STATIC) Copied from meshes_db/
│   ├── CSD_mesh_canopy.k          <-- ONLY *NODE, *ELEMENT, *SET. No *PART!
│   ├── CFD_mesh_domain.k
│   └── CFD_mesh_surface.k
│
├── 02_properties/                 <-- (DYNAMIC) Generated by Jinja2
│   └── materials_and_sections.k   <-- ONLY *MAT_... and *SECTION_... No *PART!
│
├── 03_assignments/                <-- (DYNAMIC) Generated by Jinja2
│   └── parts.k                    <-- ONLY *PART cards linking the above files
│
├── 04_mechanics/                  <-- (DYNAMIC) Generated by Jinja2
│   ├── csd_boundary.k             <-- *INITIAL_VELOCITY, *LOAD_BODY_Z
│   └── payload_mass.k             <-- *ELEMENT_MASS
│
└── 05_fluids/                     <-- (DYNAMIC) Generated by Jinja2
    ├── cfd_boundary.k             <-- *ICFD_BOUNDARY_PRESCRIBED_VEL
    └── cfd_properties.k           <-- *ICFD_MAT (Air density/viscosity injected here)

```

### 5.3. File-by-File Breakdown

1. **Static "Dumb" Meshes (01_geometry/)**

These files are pre-configured by an engineer in LS-PrePost and stored in the read-only database. The application never modifies these files.

Content: *NODE, *ELEMENT_SHELL, *SET_PART_LIST, *SET_NODE_LIST.

Strict Prohibition: They must never contain *PART, *MAT, or *SECTION cards.

2. **Dynamic Properties (02_properties/)**

Generated at runtime based on the user's dropdown selections in the UI.

Content: Defines the physical behavior.

*MAT_FABRIC (e.g., Nylon porosity, E-modulus).

*SECTION_SHELL (e.g., fabric thickness).

3. **Dynamic Assignments (03_assignments/)**

This is the critical "bridge" file generated by DynaPrep. Because the mesh and the materials are in separate files, this file links them together.

Content: Contains only the *PART cards. It maps the PID (Part ID defined in the geometry file) to the SECID (Section ID) and MID (Material ID) defined in the properties file. By isolating *PART here, the Python backend only has to write a 10-line text file to completely change the parachute's materials.

4. **Dynamic Physics Setups (04_mechanics/ & 05_fluids/)**

These .k.j2 templates are injected with user inputs (mass, altitude, velocity) at runtime to generate the actual physics boundary conditions.

Automatically calculates and injects atmospheric air density ($\rho$) and viscosity ($\mu$) based on the user's selected drop altitude into *ICFD_MAT.

Configures the payload mass (*ELEMENT_MASS_NODE_SET) and initial deployment velocity.

5. **The Master Assembly (main_run.k)**

This file contains almost no physics itself. It orchestrates the solver execution, explicitly defining the *CONTROL_TERMINATION time, the FSI coupling interfaces, and pulling the entire simulation together using include cards.

*INCLUDE: Used to pull in all the dynamically generated .k files (materials, parts, setups).

*INCLUDE_TRANSFORM: Used to pull in the static meshes from 01_geometry/. By applying automatic ID offsets (e.g., IDNOFF = 1000000, IDEOFF = 1000000) during the transform, DynaPrep mathematically guarantees that a parachute mesh and a payload mesh will never suffer from Node or Element ID collisions when combined, completely eliminating the need for manual renumbering.