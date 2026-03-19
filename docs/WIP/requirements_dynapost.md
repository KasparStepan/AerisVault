# DynaProcessing: Software Architecture & Feature Specification

## 1. Executive Summary
DynaProcessing is a standalone, high-performance Python library designed specifically for post-processing, filtering, and analyzing Fluid-Structure Interaction (FSI) parachute simulations from LS-DYNA.

Operating as the core analytical engine within the broader AerisVault ecosystem, DynaProcessing is strictly decoupled from any Graphical User Interface (GUI). It acts as a "headless" computational library that ingests raw solver outputs, applies complex engineering mathematics, and yields standardized data structures (Curves, DataFrames) and visualizations.

## 2. Software Architecture
DynaProcessing follows a modular, object-oriented architecture built on the principles of Data Decoupling and Separation of Concerns.

### 2.1. Structural Layers

- `io/` (Data Ingestion): Responsible for parsing raw, heterogeneous LS-DYNA output files (e.g., ASCII `.csv`, `.dat`), with efficient memory handling.
- `models/` (Abstractions): Contains Python dataclasses and objects representing physical entities.
  - `Curve`: Fundamental atomic unit representing a 2D time-series data array (Time vs. Value), including units, origin, and filter history.
  - `FiniteMassSimulation` and `InfiniteMassSimulation`: Object representations holding metadata and lists of parsed curves.
- `analysis/` (Computational Engine): Mathematical core, includes digital signal processors, math synthesizers, and comparison engine.
- `viz/` (Visualization): Decoupled plotting interface for generating static charts (Matplotlib for PDF reports) or data structures for interactive web rendering (Plotly).

### 2.2. Dependencies

The library is designed to be mathematically robust but lightweight, relying on industry-standard scientific packages:

- `numpy` - Core matrix and array mathematics
- `scipy` - Digital signal processing and filtering
- `pandas` - DataFrame manipulation and export
- `matplotlib` / `plotly` - Visualization generation

## 3. Core Features & Capabilities (Functional Requirements)

### 3.1. Automated Data Ingestion & Inference

- Feature: Scan a target directory and infer simulation type automatically.
- Behavior: Distinguish between Infinite Mass analyses (parsing `.dat`) and Finite Mass analyses (parsing `.csv`) without manual intervention.
- Metadata Extraction: Parse folder names or keyword files to extract metadata (e.g., initial velocity, mass).

### 3.2. Declarative Job Interface

- Feature: Single declarative Job API for users/calling applications.
- Behavior: Caller defines a configuration object with directory, variables to extract (e.g., `z_acceleration`), and transformations. Library executes pipeline internally.

### 3.3. Digital Signal Processing (DSP)

- Feature: Built-in engineering-standard digital filters for smoothing high-frequency noise from explicit FEA data.
- Supported Filters:
  - SAE CFC filters (e.g., CFC-60)
  - Butterworth low-pass filters with configurable cutoff
  - Moving average rolling window
- Traceability: Every `Curve` object stores `filter_history` for auditing of applied operations.

### 3.4. Engineering Mathematics & Aerodynamics

- Feature: Automatic unit conversions and dimensionless computations.
- Capabilities:
  - Acceleration to G-Force: flag `to_G=True` converts from `m/s^2` to `G`.
  - Aerodynamic Coefficients: compute dimensionless drag coefficient `C_d` from raw Z/X forces, with reference velocity and area inputs.

### 3.5. Simulation Comparison Engine

- Feature: `SimulationComparator` evaluates differences and convergence between simulation runs.
- Capabilities:
  - Time-series alignment via interpolation onto a common global time vector.
  - RMSE computation between base and refined simulation.
  - Difference synthesis: produce Δ-curve objects per timestep.

### 3.6. Visualization & Reporting Workflows

- Feature: Seamless export of analysis layouts.
- Capabilities:
  - Combined plotting: overlay multiple traces on unified axes.
  - Reporting: export analysis layouts into paginated PDF reports.

## 4. Non-Functional Requirements (NFRs)

### 4.1. Performance & Scalability

- Process standard LS-DYNA text output (up to 100 MB) into memory objects in < 2 seconds.
- Use vectorized `numpy`/`scipy`; no Python loops for array math.

### 4.2. Interoperability (AerisVault Integration)

- Headless execution: no `sys.exit()`, no `input()`, no blocking GUI windows.
- State independence: running same job twice yields identical results with no contamination.

### 4.3. Error Handling

- Gracefully handle corrupted/ truncated/incomplete LS-DYNA files.
- Catch exceptions, log truncation, and return valid data subset instead of crashing.
