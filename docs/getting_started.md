# Getting Started

## Prerequisites

- Python 3.10 or higher
- Git

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/KasparStepan/AerisVault.git
   cd AerisVault
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the libraries and application in editable mode:
   ```bash
   pip install -e ./libs/dynaprocessing
   pip install -e ./apps/aerisvault-ui
   ```

## Running the Application

Start the Streamlit web interface:
```bash
cd apps/aerisvault-ui
streamlit run src/aerisvault/app.py
```

The app will open in your browser (typically at `http://localhost:8501`).

## First Steps

1. **Add a simulation** — Go to the Database page, create a new simulation entry, and upload your LS-DYNA output files (`.dat` for infinite mass / wind-tunnel, `.csv` for finite mass / drop test).

2. **Analyse results** — Navigate to the Single Analysis page, select your simulation, choose curves to plot, apply filters, and view statistics and event detection.

3. **Compare simulations** — Use the Comparison page to overlay curves from multiple simulations, compute RMSE, and compare statistics side by side.

4. **Adjust settings** — The Settings page lets you configure default filter parameters and plot appearance. Settings are saved to `config.json`.

## Using DynaProcessing as a Standalone Library

You can also use the `dynaprocessing` library directly in Python scripts or Jupyter notebooks without the UI:

```python
from dynaprocessing import InfiniteMassSimulation

sim = InfiniteMassSimulation(directory_path="data/raw/sim_1/")
fpz = sim.curves["Fpz"]
fpz_filtered = fpz.apply_cfc_filter(cfc=60)
print(fpz_filtered.statistics())
```

See the [DynaProcessing README](../libs/dynaprocessing/README.md) for full API examples.
