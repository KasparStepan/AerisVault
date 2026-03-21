# DynaProcessing

**DynaProcessing** is a Python-based analysis tool designed specifically for Mechanical Engineers to extract, filter, post-process, and visualize data from LS-DYNA simulations.

It provides a highly intuitive declarative interface, allowing users to rapidly process both Infinite Mass and Finite Mass analyses with built-in support for SAE filtering, automatic unit conversions, and dimensionless aerodynamics computations (like Drag Coefficients).

---

## 🚀 Key Features

* **Declarative `Job` Interface:** Run comprehensive data post-processing via a single `Job` object. Define what directories to scan, what curves to extract, and how you want them formatted and you are ready to go.
* **Automatic Unit Conversions:** Effortlessly convert output units. Setting `to_G=True` will auto-detect curves measuring accelerations and convert them from $m/s^2$ into $G$s. Forces are uniformly reported in Newtons $[N]$.
* **Automated LS-DYNA Type Inference:** Pass the tool a directory and it will intelligently determine whether to run an `Infinite Mass` (`.dat` files) or `Finite Mass` (`.csv` files) pipeline.
* **Combined Plotting:** Visualize independent property traces on a single axis simply by flagging `combine_plots=True`. 
* **Built-in Digital Filtering:** Instantly apply SAE `CFC` channel frequency filters, `Butterworth` low-pass filters, or `Moving Average` filters dynamically to your output signals.
* **Aerodynamics Capabilities:** Calculate Dimensionless Drag Coefficients seamlessly out of standard Z/X-forces by supplying a reference velocity and working area.
* **Export Workflows:** Choose between viewing the graphical output dynamically in an interactive Jupyter environment, plotting them in standalone Matplotlib windows, or piping the entire analysis layout into a paginated `.pdf` presentation report.

---

## ⚙️ Installation

1. Clone the repository.
2. We highly recommend creating a sandboxed virtual environment before installing the requirements:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
3. Install the dependencies:
```bash
pip install -r requirements.txt
```

> **Note:** Depending on your environment, you may need to ensure `scipy` and `matplotlib` are up to date!

---

## 📖 Quick Start

The best way to understand how it works is to review the `examples/` directory. You will find both standard Python scripts (`.py`) and executed Jupyter Notebooks (`.ipynb`).

For full API documentation on how to configure your own custom analyses, read the **[Usage Guide](docs/usage.md)**.

Here is a quick snippet demonstrating how to process nodal accelerations from a Finite Mass simulation:

```python
from dynaproc.analysis.postprocess import Job

# 1. Define your job processing configuration
job = Job(
    directory="../results/finite-mass/6kg-6ms",
    variables=["z_acceleration", "resultant_velocity"],
    to_G=True,             # Converts z_acceleration (but not resultant_velocity) to Gs
    filter_type="cfc",     # Apply a CFC SAE filter
    filter_settings=60,    # CFC=60
    combine_plots=True,    # Overlay both properties on the same Matplotlib interface
    plot_settings={
        "grid_major": True,
        "grid_minor": True,
        "title": "Combined Accelerations & Velocities"
    }
)

# 2. Execute!
job.process()
```

---

## 🗂 Project Structure

* `src/dynaproc/` - Core library architecture.
  * `models/` - Curve abstractions and Infinite/Finite mass logic.
  * `io/` - CSV and `.dat` parsing interfaces.
  * `analysis/` - Post-processing `Job` API and Digital Signal filters.
* `examples/` - Working workflow examples.
* `docs/` - Technical guides and folder naming conventions.
* `results/` - Sandbox space for LS-DYNA simulation input data.

## 🤝 Contributing

Contributions, bug reports, and pull requests are welcome! If you intend to use the automated Metadata extraction, make sure to read the [Folder Naming Conventions](docs/folder_naming_conventions.md) document to see how simulation result folders should be structured.
