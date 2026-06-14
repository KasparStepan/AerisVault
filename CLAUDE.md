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
/home/kaspar/Projects/PhD/AerisVault/.venv/bin/python
```

## Common Commands

**Run dynaprocessing tests (the library with 100+ tests):**
```bash
cd libs/dynaprocessing
/home/kaspar/Projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -v
```

**Run a single test:**
```bash
cd libs/dynaprocessing
/home/kaspar/Projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_curve.py::TestCurveFiltering::test_cfc_filter_changes_values -v
```

**Run aerisvault (portal shell) tests:**
```bash
cd apps/aerisvault
/home/kaspar/Projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -v
```

**Start the Streamlit app (portal shell):**
```bash
cd apps/aerisvault
/home/kaspar/Projects/PhD/AerisVault/.venv/bin/streamlit run src/aerisvault/app.py
```

**Install a library in editable mode after changes to pyproject.toml:**
```bash
/home/kaspar/Projects/PhD/AerisVault/.venv/bin/pip install -e libs/dynaprocessing
/home/kaspar/Projects/PhD/AerisVault/.venv/bin/pip install -e apps/aerisvault
```

## Versioning

The entire monorepo uses a **single unified version**. When bumping the version, update ALL four `pyproject.toml` files to the same value:
- `pyproject.toml` (root)
- `libs/dynaprocessing/pyproject.toml`
- `libs/dynaprep/pyproject.toml`
- `apps/aerisvault/pyproject.toml`

## Architecture

This is a monorepo for post-processing LS-DYNA parachute FSI simulations. The core principle is strict separation: **libraries do all computation, the UI does none**.

```
libs/dynaprocessing/   ← analytical engine (headless, fully tested)
libs/dynaprep/         ← input deck generator (future, currently empty stub)
apps/aerisvault/       ← THE portal shell: one Streamlit app, many tool modules
apps/aerisvault-old/   ← legacy monolithic app (reference only, do not modify)
data/<key>/            ← each module owns its DB + files under data/<module_key>/
```

### Portal architecture

`apps/aerisvault` is a **portal shell**: a single Streamlit app whose landing page
lists engineering tools, each tool being a self-contained **module**. The shell
knows nothing about a module's internals — it only reads a small descriptor.

```
apps/aerisvault/src/aerisvault/
├── app.py                  ← shell entry: builds two-level navigation, runs
├── portal/
│   ├── descriptor.py       ← ModuleDescriptor dataclass (the contract)
│   ├── registry.py         ← MODULES = [...]  (single source of truth)
│   └── home.py             ← landing page: one card per module
├── shared/                 ← cross-module plumbing ONLY (no domain logic)
│   ├── paths.py            ← data_dir_for(key) → data/<key>/
│   └── navigation.py       ← pages_for_active_module(MODULES, active_key)
└── modules/
    └── fsi/                ← Parachute FSI module (formerly the whole app)
        ├── __init__.py     ← exposes MODULE (a ModuleDescriptor)
        ├── pages/          ← database, single_analysis, comparison, settings
        ├── core/           ← database.py, models.py, storage.py, config.py, bootstrap.py
        └── ui/             ← FSI-specific Streamlit components
```

Rules that keep modules sealed:
- **The module contract** is `ModuleDescriptor` (`portal/descriptor.py`): `key`,
  `title`, `icon`, `summary`, `pages` (a *callable* returning `st.Page`s, so a
  module's pages and imports load lazily, not at registry-import time), `order`.
- **Adding a tool** = create `modules/<key>/` exposing a `MODULE` descriptor, then
  append one line to `portal/registry.py`. No shell code changes.
- **Two-level navigation:** the portal home is shown until a card is clicked, which
  sets `st.session_state["active_module"]`; the shell then shows only that module's
  pages plus a "← All tools" control. `active_module` is the shell's one reserved
  session-state key.
- **Each module owns its database** under `data/<key>/`, resolved via
  `data_dir_for(key)` — never hardcode paths. FSI's DB is `data/fsi/aerisvault.db`,
  its config `data/fsi/config.json`, its files `data/fsi/raw|processed/`.
- **Session-state namespacing:** every module prefixes its keys with its `key`
  (`fsi.db`, `fsi.storage`, `fsi.settings`), initialized lazily by the module's
  `core/bootstrap.py:ensure_initialized()`, called at the top of every page's
  `render()`. This prevents one module from clobbering another's state.
- **Pages are functions, not scripts:** each page module exposes a `render()`
  function referenced by `st.Page(...)` — no top-level Streamlit body, no
  `st.set_page_config` (the shell sets it once).

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

### FSI module (apps/aerisvault/src/aerisvault/modules/fsi)

The FSI module is the former standalone UI, relocated into the portal as module #1.
Its pages live in `modules/fsi/pages/` (each exposing a `render()` function). It
stores data under `data/fsi/`: `aerisvault.db`, `config.json`, `raw/sim_{id}/`
(raw uploaded files), and `processed/sim_{id}/` (converted parquet).

Key design decisions:
- `modules/fsi/core/database.py` uses `expire_on_commit=False` and `selectinload` on all list/get queries. This is required because SQLAlchemy sessions close after each operation and returned ORM objects must remain usable (accessing `.tags` or `.files` outside the session would otherwise raise `DetachedInstanceError`).
- `StorageManager` in `modules/fsi/core/storage.py` automatically converts uploaded `.dat` files to Parquet on ingest by delegating to `dynaprocessing.io.lsdyna_csv.parse_infinite_mass_dat`.
- `modules/fsi/core/bootstrap.py:ensure_initialized()` lazily creates the DB, storage, and settings under the `fsi.*` session-state keys; every page calls it first.
- Pages import `Curve` objects from `dynaprocessing` — **no raw DataFrame manipulation in pages**.

### What does NOT exist yet
- `libs/dynaprep/` is an empty stub — out of scope, future project.
- No report generation or data export features.
- `apps/aerisvault-old/` is the legacy monolithic app — reference only, do not modify.
