# Development Guide

> **Notice:** This documentation was initially drafted with the assistance of AI to establish baseline development standards for the AerisVault ecosystem.

## 1. Prerequisites
Before you begin, ensure you have the following installed on your system:
* **Python 3.10+**
* **Git**

## 2. Environment Setup
Because AerisVault is a Monorepo, you must install the local libraries as "editable" dependencies so that the UI can access them during development.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/KasparStepan/AerisVault.git
   cd AerisVault
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the libraries and app in editable mode:**
   ```bash
   pip install -e ./libs/dynaprocessing
   pip install -e ./apps/aerisvault-ui
   ```

## 3. Running the Application Locally

To start the Streamlit UI:

```bash
cd apps/aerisvault-ui
streamlit run src/aerisvault/app.py
```

## 4. How to Add New Features

### Adding a new UI Page

AerisVault UI follows the "Thin UI" principle. Do not put heavy calculations inside Streamlit pages.

- Create a new file in `apps/aerisvault-ui/src/aerisvault/pages/` (e.g., `05_New_Tool.py`).
- Import reusable UI components from `src/aerisvault/ui/` (e.g., dropdowns, standard charts).
- Import the necessary solver logic from `dynaprocessing`.
- Keep the Streamlit script as a simple bridge between the user inputs and the backend library.

### Adding a new Filter Type to DynaProcessing

- Add the filter function to `libs/dynaprocessing/src/dynaprocessing/analysis/filters.py`.
- Add a corresponding `apply_<filter>_filter()` method to the `Curve` class in `models/curve.py`.
- Export the new function from `analysis/__init__.py` and the top-level `__init__.py`.
- Write tests in `libs/dynaprocessing/tests/`.

### Adding a new Analysis Module to DynaProcessing

- Create a new file in `libs/dynaprocessing/src/dynaprocessing/analysis/`.
- Follow the pattern of existing modules (e.g., `statistics.py`, `event_detection.py`): accept `Curve` objects as input and return dicts, floats, or new `Curve` objects.
- Export from `analysis/__init__.py` and the top-level `__init__.py`.
- Write tests with synthetic data in `libs/dynaprocessing/tests/`.

## 5. Testing

We enforce a strict `src` layout to guarantee that tests reflect the production environment.

To run tests for a specific library, navigate to its root and use pytest:

```bash
cd libs/dynaprocessing
python -m pytest tests/ -v
```

To run the UI app tests:

```bash
cd apps/aerisvault-ui
python -m pytest tests/ -v
```

**Rule:** Never import UI components into the `libs/` directories. Tests in `libs/` must be able to pass completely independently of Streamlit.
