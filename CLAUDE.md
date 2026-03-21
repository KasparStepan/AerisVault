# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## User Context

The primary developer is a **mechanical engineer**, not a software developer. Code must be:
- **Readable over clever** — prefer explicit variable names (`deployment_force`, `steady_state_time`) over abbreviations (`df`, `sst`). Avoid one-liners that compress multiple operations.
- **Self-documenting** — function and variable names should reflect engineering concepts, not computer science abstractions. A future reader will think in physics first.
- **Commented at the right level** — comments should explain *why* (the engineering intent, physical meaning, or non-obvious constraint), not *what* (the code already shows that). Example: `# Invert Z-axis: LS-DYNA outputs downward as positive, we use upward as positive` is good. `# multiply by -1` is not.
- **Flat over nested** — avoid deep class hierarchies or decorator chains. A mechanical engineer should be able to trace the logic top-to-bottom without jumping through multiple layers of abstraction.
- **Modifiable by a non-expert** — if adding a new filter type or a new analysis metric, it should be obvious where to add it and what pattern to follow.

## Environment

All commands must use the project venv:
```
/home/stepan/projects/PhD/AerisVault/.venv/bin/python
```

## Common Commands

**Run dynaprocessing tests (the library with 100+ tests):**
```bash
cd libs/dynaprocessing
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -v
```

**Run a single test:**
```bash
cd libs/dynaprocessing
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_curve.py::TestCurveFiltering::test_cfc_filter_changes_values -v
```

**Run aerisvault-ui tests:**
```bash
cd apps/aerisvault-ui
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -v
```

**Start the Streamlit app:**
```bash
cd apps/aerisvault-ui
/home/stepan/projects/PhD/AerisVault/.venv/bin/streamlit run src/aerisvault/app.py
```

**Install a library in editable mode after changes to pyproject.toml:**
```bash
/home/stepan/projects/PhD/AerisVault/.venv/bin/pip install -e libs/dynaprocessing
/home/stepan/projects/PhD/AerisVault/.venv/bin/pip install -e apps/aerisvault-ui
```

## Architecture

This is a monorepo for post-processing LS-DYNA parachute FSI simulations. The core principle is strict separation: **libraries do all computation, the UI does none**.

```
libs/dynaprocessing/   ← analytical engine (headless, fully tested)
libs/dynaprep/         ← input deck generator (future, currently empty stub)
apps/aerisvault-ui/    ← Streamlit web app (thin shell, delegates to libs)
apps/aerisvault-old/   ← legacy monolithic app (reference only, do not modify)
```

### dynaprocessing library

The fundamental unit is the **`Curve`** (`models/curve.py`) — an immutable time-series container. All filter and transform operations return a **new** Curve, never mutating the original. This is important: never try to modify a Curve in-place.

Data flow through the library:
1. `io/lsdyna_csv.py` parses raw LS-DYNA output files (`.dat` for infinite mass / ICFD, `.csv` for finite mass) into lists of `Curve` objects.
2. `models/infinite_mass.py` and `models/finite_mass.py` wrap the parsers — they take a **directory path**, auto-discover the result files, and expose curves via `.curves` dict and convenience properties (`.fpx`, `.fpy`, `.fpz`).
3. `analysis/` modules operate on `Curve` objects: `filters.py`, `statistics.py`, `event_detection.py`, `derivatives.py`, `comparison.py`.
4. `viz/plot_utils.py` produces Plotly figures from lists of Curves.

Key APIs to know:
- `InfiniteMassSimulation(directory_path=...)` — takes the **directory** containing `.dat` files, not the file itself. Raises `FileNotFoundError` if directory missing.
- `sim.curves` — `Dict[str, Curve]` keyed by column name (e.g. `"Fpz"`, `"Fpx"`)
- `curve.apply_cfc_filter(cfc=60)` — returns new filtered Curve
- `curve.statistics()` — returns dict with keys: `mean`, `std`, `min`, `max`, `rms`, `median`
- `curve.derivative(order=1)` — returns new Curve
- `auto_detect_events(curve)` — returns dict with keys: `deployment`, `inflation`, `steady_state`, `oscillations`

### aerisvault-ui app

Pages are in `src/aerisvault/pages/` (Streamlit multipage convention). The app stores data in `data/raw/sim_{id}/` (raw uploaded files) and `data/processed/sim_{id}/` (converted parquet).

Key design decisions:
- `core/database.py` uses `expire_on_commit=False` and `selectinload` on all list/get queries. This is required because SQLAlchemy sessions close after each operation and returned ORM objects must remain usable (accessing `.tags` or `.files` outside the session would otherwise raise `DetachedInstanceError`).
- `StorageManager` in `core/storage.py` automatically converts uploaded `.dat` files to Parquet on ingest by delegating to `dynaprocessing.io.lsdyna_csv.parse_infinite_mass_dat`.
- Pages import `Curve` objects from `dynaprocessing` — **no raw DataFrame manipulation in pages**.

### What does NOT exist yet
- `libs/dynaprep/` is an empty stub — out of scope, future project.
- No report generation or data export features.
- `apps/dynaprocessing/` inside `apps/` is a leftover artefact — ignore it.
