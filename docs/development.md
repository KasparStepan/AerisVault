# Development & Contribution Guide

> **Notice:** This documentation was initially drafted with the assistance of AI to establish baseline development standards for the AerisVault ecosystem.

Welcome to the AerisVault development guide! This document outlines how to set up your local environment, run the applications, and safely contribute to the codebase.

## 1. Prerequisites
Before you begin, ensure you have the following installed on your system:
* **Python 3.10+**
* **Git**
* A modern Python workspace manager like **`uv`** (recommended) or **`poetry`**.
* *(Optional)* LS-Dyna solver and LS-PrePost for local mesh testing.

## 2. Environment Setup
Because AerisVault is a Monorepo, you must install the local libraries as "editable" dependencies so that the UI can access them during development.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/aerisvault.git
   cd aerisvault
   ```

2. **Setup the Workspace (using uv or pip):**
   Ensure your virtual environment is active, then install the local libraries into the UI app:

   ```bash
   pip install -e ./libs/dynaprep
   pip install -e ./libs/dynaprocessing
   pip install -r ./apps/aerisvault-ui/requirements.txt
   ```
## 3. Running the Application locally

To start the Streamlit UI:

```bash
cd apps/aerisvault-ui
streamlit run src/aerisvault/app.py
```
## 4. How to Add New Features

### Adding a new UI Page (Tool)

AerisVault UI follows the "Thin UI" principle. Do not put heavy calculations inside Streamlit pages.

- Create a new file in apps/aerisvault-ui/src/aerisvault/pages/ (e.g., 04_New_Tool.py).
- Import reusable UI components from src/aerisvault/ui/ (e.g., dropdowns, standard charts).
- Import the necessary solver logic from dynaprep or dynaprocessing.
- Keep the Streamlit script as a simple bridge between the user inputs and the backend libraries.

### Adding a new LS-Dyna Template

If you want to support a new type of analysis:

- Navigate to libs/dynaprep/src/dynaprep/templates/.
- Create a new Jinja2 template (e.g., new_material.k.j2).
- Ensure you use strict string formatting (e.g., {{ '%10s' % variable }}) to respect LS-Dyna's 10-character column limits.
- Update generator.py to map Python arguments to your new template.

## 5. Testing

We enforce a strict src layout to guarantee that tests reflect the production environment.

To run tests for a specific library, navigate to its root and use pytest:

```bash
cd libs/dynaprocessing
pytest tests/
```

**Rule:** Never import UI components into the libs/ directories. Tests in libs/ must be able to pass completely independently of Streamlit.