# DynaProcessing: Software Architecture & Feature Specification

> **Status:** All features described below are **implemented** unless noted otherwise.

## 1. Executive Summary
**DynaProcessing** is a standalone Python library designed specifically for post-processing, filtering, and analyzing Fluid-Structure Interaction (FSI) parachute simulations from LS-DYNA.

Operating as the core analytical engine within the broader AerisVault ecosystem, DynaProcessing is strictly decoupled from any Graphical User Interface (GUI). It acts as a "headless" computational library that ingests raw solver outputs (`.dat` and `.csv` files), applies complex engineering mathematics, and yields standardized data structures (immutable `Curve` objects) and visualizations.

## 2. Software Architecture
DynaProcessing follows a modular, object-oriented architecture built on the principles of Data Decoupling and Separation of Concerns.

### 2.1. Structural Layers
* **`io/` (Data Ingestion):** Responsible for parsing raw, heterogeneous LS-DYNA output files (e.g., ASCII `.csv`, `.dat`). It handles the heavy lifting of reading files into memory efficiently.
* **`models/` (Abstractions):** Contains Python dataclasses and objects representing physical entities. 
  * `Curve`: The fundamental atomic unit representing a 2D time-series data array (Time vs. Value) including its units, origin, and filter history.
  * `FiniteMassSimulation` & `InfiniteMassSimulation`: Object representations holding metadata and lists of parsed curves.
* **`analysis/` (Computational Engine):** The mathematical heart of the library. It contains digital signal processors, math synthesizers, and the comparison engine.
* **`viz/` (Visualization):** A decoupled plotting interface capable of generating static charts (Matplotlib for PDF reports) or returning data structures ready for interactive web rendering (Plotly).

### 2.2. Dependencies
The library is designed to be mathematically robust but lightweight, relying strictly on industry-standard scientific packages:
* **`numpy`**: Core matrix and array mathematics.
* **`scipy`**: Digital signal processing and filtering.
* **`pandas`**: Dataframe manipulation and export.
* **`matplotlib` / `plotly`**: Visualization generation.

---

## 3. Core Features & Capabilities (Functional Requirements)

### 3.1. Automated Data Ingestion & Inference
* **Feature:** The library must be able to scan a target directory and automatically infer the simulation type.
* **Behavior:** It intelligently distinguishes between `Infinite Mass` analyses (parsing `.dat` output files) and `Finite Mass` analyses (parsing `.csv` files) without manual user intervention.
* **Metadata Extraction:** It must automatically parse folder names or keyword files to extract metadata (e.g., initial velocity, mass).

### 3.2. Declarative `Job` Interface
* **Feature:** Users (or calling applications) interact with the library via a single, declarative `Job` API.
* **Behavior:** Instead of writing complex loops, the caller defines a configuration object specifying the target directory, the variables to extract (e.g., `z_acceleration`), and the required transformations. The library executes the entire pipeline internally.

### 3.3. Digital Signal Processing (DSP)
* **Feature:** The library must provide built-in, engineering-standard digital filters to smooth high-frequency noise inherent in explicit FEA codes like LS-DYNA.
* **Supported Filters:**
  * **SAE CFC Filters:** Industry-standard Channel Frequency Class filters (e.g., CFC-60) specifically tailored for crash and drop-test accelerations.
  * **Butterworth Filters:** Standard low-pass filters with configurable cutoff frequencies.
  * **Moving Average:** Simple rolling window aggregations.
* **Traceability:** Every `Curve` object must permanently log its `filter_history` so the user always knows what mathematical operations were applied to the raw data.

### 3.4. Engineering Mathematics & Aerodynamics
* **Feature:** Automatic unit conversions and dimensionless computations.
* **Capabilities:**
  * **Acceleration to G-Force:** Setting a flag (`to_G=True`) automatically identifies acceleration curves in **m/s²** and converts them to standard Gravity units (**G**).
  * **Aerodynamic Coefficients:** Calculates Dimensionless Drag Coefficients (**Cd**) from raw Z/X-forces by accepting inputs for reference velocity and parachute reference area.

### 3.5. Simulation Comparison Engine
* **Feature:** A dedicated mathematical comparator module (`SimulationComparator`) to evaluate differences and convergence between multiple distinct simulation runs.
* **Capabilities:**
  * **Time-Series Alignment:** Mathematically interpolates curves from simulations with different timesteps and resolutions onto a single, standardized global time vector.
  * **RMSE Calculation:** Computes the Root Mean Square Error between a base reference simulation and refined meshes to evaluate mesh convergence.
  * **Difference Synthesis:** Generates brand-new `Curve` objects representing the exact mathematical difference (**Δ**) between two properties at every timestep.

### 3.6. Visualization & Reporting Workflows
* **Feature:** Seamless export of analysis layouts.
* **Capabilities:**
  * **Combined Plotting:** Ability to overlay independent property traces (e.g., multiple node accelerations) onto a single standardized axis.
  * **Reporting:** Capability to pipe the entire analysis layout into a paginated `.pdf` presentation report for engineering sign-offs.

---

## 4. Non-Functional Requirements (NFRs)

### 4.1. Performance & Scalability
* The library must process standard LS-DYNA text outputs (up to 100 MB) and convert them into internal memory objects in under 2 seconds.
* Time-series alignments and filtering operations must utilize vectorized `numpy` and `scipy` functions; standard `for-loops` are prohibited for array math to ensure rapid execution.

### 4.2. Interoperability (AerisVault Integration)
* **Headless Execution:** The library must never call `sys.exit()`, prompt for `input()`, or open blocking GUI windows by default. It must return variables and figures so the parent application (e.g., AerisVault Streamlit App) can control the display.
* **State Independence:** The library must be stateless. Running a `Job` twice on the same data must yield identically reproducible results without memory leaks or data contamination between runs.

### 4.3. Error Handling
* The library must gracefully handle corrupted, truncated, or incomplete LS-DYNA result files (common in aborted FSI runs) by catching exceptions, logging the truncation time, and returning the valid subset of data rather than crashing the application.