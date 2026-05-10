# AerisVault Aircraft CFD Module — v1 Design

**Status:** Draft (awaiting Stepan's review)
**Date:** 2026-05-10
**Authors:** Stepan + Claude (brainstorming session)
**Related work package:** [`docs/WorkPackages/CFD.md`](../../WorkPackages/CFD.md)

---

## 1. Overview

This document is the v1 design for the planned `aerocfd` module of AerisVault — a structured engineering database and analysis environment for steady aircraft CFD polars produced by ANSYS Fluent. It is the result of a brainstorming session and consolidates eight design sections approved one by one by Stepan.

The module follows the existing AerisVault philosophy: the analytical library (`libs/aerocfd/`) does all the computation; the Streamlit app (`apps/aerocfd-ui/`) is a thin shell that delegates to it.

For the engineering rationale (why raw loads, why fixed Fluent reports, why the Aircraft → OperatingCondition → AlphaCase hierarchy), see the work package. **This document focuses on the implementation decisions** — what to build, in what order, and who writes which parts.

## 2. Collaboration model

This is a learning project for Stepan. Work proceeds module-by-module with an explicit per-module split:

- **Stepan writes** the parts where engineering understanding matters: `Polar` class, body→wind rotation, pitching-moment sign flip, coefficient calculations, group/total summation, hand-checked rotation tests.
- **Claude writes** the mechanical scaffolding: SQLAlchemy ORM models and session helpers, file I/O glue, Streamlit page skeletons, test fixtures and parametrize boilerplate, plot helpers around Plotly.
- The split is per-module, not absolute. Before each new module the two of us agree explicitly which side writes it.

Discussion is the default mode; autonomous code generation is not. Slow iterations beat one big handoff — the point is the learning, not just the artifact.

## 3. Scope

### 3.1 In v1

- One aircraft at a time, with reference values (`S_ref`, `c_ref`, `b_ref`, axis convention).
- Fixed-setup operating conditions (one Fluent setup, only α varies between cases).
- Multiple α cases per operating condition forming an aerodynamic polar.
- Raw force/moment storage in body frame; coefficients derived in the library.
- Body→wind rotation in the library (rotation is **not** redefined in Fluent per case).
- Pitching-moment sign flip in the library (Fluent's My is nose-down in this convention; aerospace Cm is nose-up).
- Aircraft parts (CFD extraction zones) and engineering groups (analysis-facing assemblies).
- Manual `Cm(α)` entry at user-defined CG positions (Path A).
- Comparison module: overlay polars, delta tables, CSV export.

### 3.2 Out of v1, deferred (planned, not abandoned)

- **Path B — analytical Cm transfer** from raw moments and per-part surface centers. The math is implemented in slice 4 and tested; the schema (`aircraft_part.moment_ref_*`) is prepared. The UI does not call it until Fluent surface centers are exported. Lights up post-v1 with no schema migration.
- Fluent CSV importers (`aerocfd/io/`).
- File attachments (`StorageManager`, `raw/processed/`).
- Tags and full-text search.
- The separate `apps/simtracker-ui/` job-tracking app.

### 3.3 Out of v1, abandoned (not coming back unless reopened)

- Sideslip (β ≠ 0). v1 stays in the x–z plane.
- Control-surface deflection sweeps.
- Mesh-convergence and uncertainty quantification.
- Cluster scheduler integration.
- Automated PDF report generation.
- Snapshotting / freezing reference values to protect existing polars (replaced by non-blocking UI warnings).
- Multi-user features (auth, RBAC, audit logs, conflict resolution).

## 4. Architecture

### 4.1 Repository placement

```
AerisVault/
├── libs/
│   ├── dynaprocessing/        ← unchanged
│   └── aerocfd/               ← NEW (computation library)
├── apps/
│   ├── aerisvault-ui/         ← unchanged
│   └── aerocfd-ui/            ← NEW (Streamlit app)
└── data/
    └── aerocfd/               ← NEW (database file from slice 2 on)
```

### 4.2 Two libraries side by side, never coupled

`aerocfd` does not import from `dynaprocessing`, and vice versa. They share patterns and conventions, no code.

### 4.3 Single-user posture

Current state: Stepan is the only user. Future expectation: other users may use individual tools (e.g. only `aerocfd-ui`), which is why the database is separate from `aerisvault-ui`'s. Mutable-state hazards (e.g. editing `S_ref` after polars are computed) get **non-blocking UI warnings**, not snapshotting/freezing — proportional to single-user reality.

### 4.4 Versioning

The monorepo's single unified version is bumped uniformly on `aerocfd` releases per the existing rule in `CLAUDE.md`. New `pyproject.toml` files (`libs/aerocfd/pyproject.toml`, `apps/aerocfd-ui/pyproject.toml`) join the existing four in the version-bump checklist.

### 4.5 Build order: vertical slice progression

v1 is delivered as five stacked slices. Each slice is shippable end-to-end; nothing in slice N is removed by slice N+1, only added or refactored.

| # | Slice | What ships |
|---|---|---|
| 1 | Library + single Streamlit page, no DB | CL/CD/L/D/CL–CD/Cm from total loads, plotted in browser |
| 2 | Database & multipage app | SQLite + SQLAlchemy persistence; pages split per concern |
| 3 | Parts & engineering groups | Per-part loads, group summation in wind frame |
| 4 | Cm dual path | Multi-CG manual `Cm(α)` (Path A); analytical Path B prepared but inert |
| 5 | Comparison | Overlay polars, delta tables, CSV export |

Each slice is detailed in §10.

## 5. Library structure

### 5.1 Folder layout (mirrors `dynaprocessing`)

```
libs/aerocfd/src/aerocfd/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── polar.py                 # Polar — 1D series indexed by alpha
│   ├── dataset.py               # AeroDataset — orchestrator
│   ├── aircraft.py              # Aircraft dataclass
│   ├── operating_condition.py   # OperatingCondition dataclass
│   ├── alpha_case.py            # AlphaCase dataclass (gains part_loads field in slice 3)
│   ├── aircraft_part.py         # Part, PartGroup, PartLoad (slice 3)
│   └── (slice 4 may add small types as needed)
├── analysis/
│   ├── __init__.py
│   ├── rotation.py              # body→wind rotation, Cm sign flip
│   ├── coefficients.py          # CL, CD, L/D, Cm formulas
│   ├── summation.py             # (slice 3) sum_part_loads, group resolution
│   ├── moment_transfer.py       # (slice 4) M_cg = M_ref + r × F
│   └── comparison.py            # (slice 5)
├── viz/
│   ├── __init__.py
│   └── plot_utils.py            # plotly figure helpers
└── io/
    └── __init__.py              # empty in v1; populated by future importers
```

### 5.2 The library is ORM-free

It never imports SQLAlchemy or anything from `apps/aerocfd-ui/`. ORM models live entirely in the UI app and are translated to/from the library's plain dataclasses by mapper functions.

## 6. Data model

### 6.1 `Polar` — 1D series indexed by α

Small, immutable, mirrors the shape of `dynaprocessing`'s `Curve` but with α as the independent variable. **Stepan writes this** as the primary learning artifact.

```python
class Polar:
    """1D ordered series indexed by angle of attack."""
    def __init__(
        self,
        alpha_deg: np.ndarray,
        values: np.ndarray,
        name: str = "Unknown",
        units: str | None = None,
        metadata: dict | None = None,
    ): ...
    @property
    def alpha_deg(self) -> np.ndarray: ...
    @property
    def values(self) -> np.ndarray: ...
    def interpolate_at(self, alpha_deg: float) -> float: ...
    def slice_alpha(self, alpha_min: float, alpha_max: float) -> "Polar": ...
```

Methods like `cl_max`, `alpha_at_cl_max`, `alpha_at_ld_max` are deliberately **not** added on day one. They get added when first needed, not speculatively.

### 6.2 `AeroDataset` — orchestrator

Mirrors `dynaprocessing.models.InfiniteMassSimulation`. Holds raw loads + references, produces `Polar` instances on demand. **Stepan writes this.**

```python
class AeroDataset:
    """Aerodynamic dataset for one operating condition."""
    def __init__(
        self,
        aircraft: Aircraft,
        operating_condition: OperatingCondition,
        alpha_cases: list[AlphaCase],
    ): ...
    @property
    def alpha_deg(self) -> np.ndarray: ...
    @property
    def dynamic_pressure_pa(self) -> float: ...
    def lift(self) -> Polar: ...      # Newtons
    def drag(self) -> Polar: ...      # Newtons
    def cl(self) -> Polar: ...
    def cd(self) -> Polar: ...
    def lift_to_drag(self) -> Polar: ...
    def cm(self) -> Polar: ...        # at Fluent's moment ref point in slice 1
    # slice 3 adds: cl_for_group(name), cd_for_group(name), ...
    # slice 4 changes cm() to take optional cg argument
```

### 6.3 Plain dataclasses

`@dataclass(frozen=True)` so accidental mutation fails loudly.

```python
@dataclass(frozen=True)
class Aircraft:
    name: str
    s_ref_m2: float
    c_ref_m: float
    b_ref_m: float
    axis_convention: str = "x_fwd_z_up_rh"
    description: str = ""

@dataclass(frozen=True)
class OperatingCondition:
    name: str
    velocity_mps: float
    density_kgpm3: float
    description: str = ""
    # turbulence_model, turbulence_bc_method, ... added when needed

@dataclass(frozen=True)
class AlphaCase:
    alpha_deg: float
    fx_n: float                 # body frame, total
    fz_n: float                 # body frame, total
    my_nm: float                # raw Fluent My; sign flip in library, not storage
    convergence_status: ConvergenceStatus = ConvergenceStatus.UNKNOWN
    notes: str = ""
```

In slice 3, `AlphaCase` is refactored: the inline force fields are replaced by a `part_loads: list[PartLoad]` field, and totals are derived. Stepan does this refactor as the schema-evolution learning moment.

### 6.4 Units

SI throughout: meters, Newtons, Newton-metres, seconds, kilograms per cubic metre, metres per second. Field names carry the unit suffix (`_m`, `_n`, `_nm`, `_kgpm3`, `_mps`) to make this self-documenting.

## 7. The math

### 7.1 Axis convention

- **Body frame:** x = forward, z = up, right-handed → y points to the **left**.
- **α positive = nose up** (standard aerospace).
- **Fluent setup is fixed:** force/moment reports are always in this body frame, regardless of α. Stepan never redefines monitors when α changes.
- **Sideslip ignored in v1** (β = 0). Math stays in the x–z plane; Fy/Mx/Mz are stored as zeros (slice 3+) or absent (slice 1).

### 7.2 Body → wind rotation

`analysis/rotation.py`. Pure function, numpy throughout (works for scalar α or array α via broadcasting):

```python
import numpy as np

def body_to_wind(fx_n, fz_n, alpha_deg):
    """Rotate body-frame total force to wind frame.
    Returns (drag_n, lift_n)."""
    a = np.radians(alpha_deg)
    drag_n =  fx_n * np.cos(a) + fz_n * np.sin(a)
    lift_n = -fx_n * np.sin(a) + fz_n * np.cos(a)
    return drag_n, lift_n
```

### 7.3 Pitching-moment sign flip

Same module, separate named function so the convention is self-documenting:

```python
def fluent_my_to_aero(my_fluent_nm):
    """Convert Fluent's right-hand-rule My (nose-DOWN positive in this axis
    convention) to the aerospace Cm sign convention (nose-UP positive)."""
    return -my_fluent_nm
```

### 7.4 Coefficients

`analysis/coefficients.py`. Pure functions, numpy-friendly:

```python
def dynamic_pressure(density_kgpm3, velocity_mps):
    return 0.5 * density_kgpm3 * velocity_mps**2

def cl(lift_n, q_pa, s_ref_m2):
    return lift_n / (q_pa * s_ref_m2)

def cd(drag_n, q_pa, s_ref_m2): ...
def cm(my_aero_nm, q_pa, s_ref_m2, c_ref_m): ...
def lift_to_drag(lift_n, drag_n): ...   # element-wise; drag_n == 0 → np.inf
```

### 7.5 Group summation: rotate first, sum later

When parts arrive in slice 3, the library **rotates each part's loads to wind frame first**, then sums in wind frame. Mathematically equivalent to summing in body frame and then rotating (rotation is linear), but engineering questions (*"what does the wing contribute to lift?"*) live in wind frame, so the code reads naturally as:

```python
group_lift = sum(part.lift for part in group.parts)
```

Coefficients are **never summed** — each part's coefficient is normalized by the same `S_ref`, and the contribution to total CL is the part's lift divided by `q∞ · S_ref`. The additivity rule applies to forces, not coefficients.

### 7.6 The gold tests (the spine)

Three tests in `tests/test_rotation.py` are the spine of the whole library. They must pass at all times after slice 1; if they ever fail without an intentional convention change, there is a real bug:

1. **Zero-α passthrough.** `body_to_wind(fx, fz, 0.0) == (fx, fz)`.
2. **Pure vertical force at α = 10°.** `body_to_wind(0.0, 1000.0, 10.0)` returns `D = 1000·sin(10°)`, `L = 1000·cos(10°)`.
3. **Stable airfoil sign-flip.** Given a positive Fluent My (nose-down in this convention), `fluent_my_to_aero` returns negative; `dataset.cm()` for a stable-airfoil case returns negative Cm.

Written in slice 1, never deleted.

## 8. Database schema

### 8.1 Technology

- **SQLite** + **SQLAlchemy** (same version as `aerisvault-ui`).
- One DB file: `data/aerocfd/aerocfd.db`. Separate from `aerisvault-ui`'s database to anticipate per-tool user separation.
- Session pattern mirrors `aerisvault-ui` exactly: `expire_on_commit=False`, `selectinload` on every list/get query for relationships.

### 8.2 ORM placement

```
libs/aerocfd/                          ← pure Python types, no ORM
└── src/aerocfd/models/                @dataclass(frozen=True)

apps/aerocfd-ui/                       ← ORM lives here
└── src/aerocfd_ui/core/
    ├── database.py                    session helpers
    ├── models.py                      AircraftORM, OperatingConditionORM, ...
    └── mappers.py                     ORM ↔ dataclass mappers
```

### 8.3 Slice 2 schema

```
aircraft
  id              INTEGER PK
  name            TEXT NOT NULL
  description     TEXT
  s_ref_m2        REAL NOT NULL
  c_ref_m         REAL NOT NULL
  b_ref_m         REAL NOT NULL
  axis_convention TEXT NOT NULL DEFAULT 'x_fwd_z_up_rh'
  created_at      DATETIME

operating_condition
  id                       INTEGER PK
  aircraft_id              INTEGER FK → aircraft.id
  name                     TEXT NOT NULL
  description              TEXT
  velocity_mps             REAL NOT NULL
  density_kgpm3            REAL NOT NULL
  pressure_pa              REAL
  altitude_m               REAL
  turbulence_model         TEXT
  turbulence_bc_method     TEXT
  turbulence_intensity_pct REAL
  turbulent_viscosity_ratio REAL
  notes                    TEXT

alpha_case
  id                     INTEGER PK
  operating_condition_id INTEGER FK → operating_condition.id
  alpha_deg              REAL NOT NULL
  case_name              TEXT
  convergence_status     TEXT NOT NULL DEFAULT 'unknown'
  iteration_count        INTEGER
  notes                  TEXT
  fx_n                   REAL    ← TOTAL Fx (Fluent body frame); removed in slice 3
  fz_n                   REAL    ← TOTAL Fz; removed in slice 3
  my_nm                  REAL    ← raw Fluent My; sign flip in library, not stored
```

`convergence_status` is a Python-side enum with values: `converged`, `partially_converged`, `oscillating`, `diverged`, `stopped_manually`, `unknown`. Stored as TEXT.

### 8.4 Slice 3 schema additions

```
aircraft_part
  id            INTEGER PK
  aircraft_id   INTEGER FK
  name          TEXT NOT NULL
  description   TEXT
  display_order INTEGER

aircraft_part_group
  id          INTEGER PK
  aircraft_id INTEGER FK
  name        TEXT NOT NULL
  description TEXT

aircraft_part_group_member
  group_id INTEGER FK
  part_id  INTEGER FK
  PRIMARY KEY (group_id, part_id)

alpha_case_part_load
  id            INTEGER PK
  alpha_case_id INTEGER FK
  part_id       INTEGER FK
  fx_n REAL  fy_n REAL  fz_n REAL
  mx_nm REAL my_nm REAL mz_nm REAL
  UNIQUE (alpha_case_id, part_id)
```

Slice 3 **drops** `fx_n, fz_n, my_nm` from `alpha_case`. Two acceptable approaches in a single-user learning context, both delivered by Stepan:
- **"Wipe and re-enter."** Delete the SQLite file, let SQLAlchemy recreate the schema from scratch, re-enter test data. Simplest; no migration script needed.
- **Migration script.** Read existing slice-2 DB, create the new tables, copy each `alpha_case`'s totals into a single "total" pseudo-part row in `alpha_case_part_load`, drop the old columns. More work, more learning value if Stepan wants schema-evolution practice.

All six force/moment components stored even though v1 only uses Fx/Fz/My — schema future-proofing for a deferred sideslip extension. Fy/Mx/Mz are stored as zeros for now.

### 8.5 Slice 4 schema additions

Add to `aircraft_part` (NULL until Fluent surface centers are exported):
```
moment_ref_x_m REAL NULL
moment_ref_y_m REAL NULL
moment_ref_z_m REAL NULL
```

New table:
```
alpha_case_manual_cm
  id            INTEGER PK
  alpha_case_id INTEGER FK
  cg_over_mac   REAL NOT NULL
  cm_value      REAL NOT NULL
  source        TEXT NOT NULL    ← 'manual' or 'derived'
  source_label  TEXT             ← optional free-text note
  UNIQUE (alpha_case_id, cg_over_mac, source)
```

The UNIQUE constraint lets manual and derived values for the same (case, CG) coexist for side-by-side sanity checks.

### 8.6 Single-user warnings (UI side, not DB-enforced)

- Editing `s_ref_m2`, `c_ref_m`, or `b_ref_m` on an aircraft → warn that existing polars referencing this aircraft were computed with the previous values; recompute or create a new aircraft for comparison.
- Deleting an `aircraft_part` that has `alpha_case_part_load` rows → warn and require explicit confirm.
- Changing `axis_convention` → block. This is a breaking convention change; require a new aircraft.

## 9. UI app (`apps/aerocfd-ui/`)

### 9.1 App layout

```
apps/aerocfd-ui/
├── pyproject.toml
├── src/aerocfd_ui/
│   ├── __init__.py
│   ├── app.py                          ← Streamlit entry (slice 1: full app; slice 2+: home page)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                   ← paths, constants
│   │   ├── database.py                 ← session helpers (slice 2+)
│   │   ├── models.py                   ← SQLAlchemy ORM (slice 2+)
│   │   ├── mappers.py                  ← ORM ↔ dataclass (slice 2+)
│   │   └── storage.py                  ← future: file attachments
│   ├── pages/                          ← Streamlit multipage convention (slice 2+)
│   └── ui/
│       └── components.py               ← reusable widgets (e.g. aircraft_picker)
└── tests/
```

### 9.2 Slice 1 — single page, no DB

The whole app is `app.py`. Top-to-bottom layout:

1. **Aircraft section** — `st.number_input` for `s_ref_m2`, `c_ref_m`, `b_ref_m`; `st.text_input` for `name`. Pre-filled with reasonable defaults.
2. **Operating-condition section** — `st.number_input` for `velocity_mps`, `density_kgpm3`. Pre-filled.
3. **Alpha-cases table** — `st.data_editor` with columns `alpha_deg`, `fx_n`, `fz_n`, `my_nm`, `convergence_status` (dropdown). Starts with 5 default rows.
4. **"Plot" button** — builds dataclasses from form values, instantiates `AeroDataset`, renders five Plotly figures: CL–α, CD–α, L/D–α, CL–CD polar, **Cm–α** (at Fluent's moment reference point).

No persistence; refreshing the page resets to defaults.

### 9.3 Slice 2+ — multipage

```
pages/
├── 01_aircraft.py              # create/edit/delete aircraft, edit refs
├── 02_operating_conditions.py  # OCs for selected aircraft
├── 03_data_entry.py            # α cases for selected OC
├── 04_analysis.py              # plots from DB-loaded data
├── 05_comparison.py            # (slice 5)
└── 06_settings.py
```

Cross-page state via `st.session_state`: `current_aircraft_id`, `current_operating_condition_id`. A picker component in `ui/components.py` puts this at the top of relevant pages.

### 9.4 Plot conventions

- **Library returns Plotly `Figure` objects** from `aerocfd/viz/plot_utils.py`. One function per figure: `cl_alpha_figure(polar)`, `cd_alpha_figure(polar)`, `lift_to_drag_alpha_figure(polar)`, `drag_polar_figure(cl_polar, cd_polar)`, `cm_alpha_figure(polar)`.
- **UI never builds Plotly figures directly.** Pages call the helper and pass the figure to `st.plotly_chart(fig, use_container_width=True)`.
- v1 styling: default Plotly theme, axis labels with units, title from the polar's `name`. No custom colors yet.

### 9.5 Streamlit testing

Streamlit pages are **not unit-tested** in v1. Same approach `aerisvault-ui` already uses. The library underneath has full coverage; the page can only break in glue ways, which are findable by browser inspection in seconds.

## 10. Slice progression in detail

### 10.1 Slice 1 — CL/CD/L/D/CL–CD/Cm from totals, no DB

**Goal:** prove body→wind rotation and Cm sign-flip end-to-end on a tiny dataset, in a real Streamlit page.

**Library files (Stepan):**
- `models/polar.py`, `models/aircraft.py`, `models/operating_condition.py`, `models/alpha_case.py`, `models/dataset.py`
- `analysis/rotation.py` — `body_to_wind`, `fluent_my_to_aero`
- `analysis/coefficients.py` — `dynamic_pressure`, `cl`, `cd`, `cm`, `lift_to_drag`

**Library files (Claude):**
- `viz/plot_utils.py` — five figure helpers

**App files (Claude):**
- `apps/aerocfd-ui/src/aerocfd_ui/app.py` — single page

**Tests written first (Stepan writes assertions; Claude writes fixtures on request):**
- `test_polar.py`, `test_rotation.py` (the gold tests), `test_coefficients.py`, `test_dataset.py`

**Definition of done:** open the app in the browser, see five plots from default-filled form, edit the table, see plots update.

### 10.2 Slice 2 — Database & multipage app

**Goal:** persist aircraft, OCs, α cases between sessions; convert app to multipage.

**Library changes:** none.

**App files (Claude):**
- `core/database.py`, `core/models.py`, `core/mappers.py`, `core/config.py`
- `pages/01_aircraft.py`, `02_operating_conditions.py`, `03_data_entry.py`, `04_analysis.py`, `06_settings.py`
- `ui/components.py` — `aircraft_picker`, `operating_condition_picker`
- `app.py` becomes the home/landing page

**Tests added:**
- `tests/test_mappers.py` — round-trip `dataclass → ORM → dataclass` preserves all fields
- `tests/test_database.py` — basic CRUD smoke tests

**Single-user warning added** in `01_aircraft.py` for ref-value edits.

**Definition of done:** create aircraft → OC → α cases → close app → reopen → same data, same plots.

### 10.3 Slice 3 — Parts & engineering groups

**Goal:** raw loads stored per-part; groups defined; per-part and per-group plots.

**The schema migration moment.** Stepan writes the script that drops `fx_n/fz_n/my_nm` from `alpha_case` and moves data to `alpha_case_part_load` (or "wipe and re-enter").

**Library files (Stepan):**
- `models/aircraft_part.py` — `Part`, `PartGroup` dataclasses
- `analysis/summation.py` — `sum_part_loads`, group resolution
- `models/dataset.py` — refactored: `AeroDataset` still takes `list[AlphaCase]`, but each `AlphaCase` now exposes `part_loads`; `AeroDataset` gains `cl_for_group(name)` and similar group methods.
- `models/alpha_case.py` — refactored: inline force fields removed, `part_loads` field added

**App files (Claude):**
- `core/models.py` — `AircraftPartORM`, `AircraftPartGroupORM`, `AircraftPartGroupMemberORM`, `AlphaCasePartLoadORM`
- `core/mappers.py` — extended
- `pages/01_aircraft.py` — gains "Parts & Groups" section
- `pages/03_data_entry.py` — gains per-part input mode (UX decision deferred to implementation)
- `pages/04_analysis.py` — gains group selector

**Tests added:**
- `test_summation.py` — sum a known set of parts, check totals
- `test_dataset.py` — extended for per-group cl/cd
- migration script gets its own test against a fixture DB

**Definition of done:** define wing/slot/trailing-edge as parts, group as "wing system", enter per-part loads, plot CL contribution from any group.

### 10.4 Slice 4 — Cm dual path

**Goal:** multi-CG `Cm(α)` overlay; manual entry workflow (Path A); analytical path (Path B) prepared but inert.

**Library files (Stepan):**
- `analysis/moment_transfer.py` — `M_cg = M_ref + r × F`. Implemented and tested even though the UI doesn't call it yet.
- `models/dataset.py` — `cm()` gains optional `cg_over_mac` argument

**App files (Claude):**
- `core/models.py` — `AlphaCaseManualCmORM`; `moment_ref_x_m/y_m/z_m` added to `AircraftPartORM`
- `pages/03_data_entry.py` — "Manual Cm" section: list of CG positions defined per aircraft; `data_editor` for Cm values
- `pages/04_analysis.py` — multi-curve `Cm(α)` overlay with `source` tag in legend
- `pages/01_aircraft.py` — UI for defining per-aircraft CG positions

**Tests added:**
- `test_moment_transfer.py` — hand-checked `M_cg = M_ref + r × F` cases
- `test_manual_cm_storage.py` — round-trip mapper

**Definition of done:** for one aircraft and one OC, enter manual Cm at three CG positions; see all three curves overlaid on `04_analysis.py`. Path B remains dormant — `aircraft_part.moment_ref_*` columns NULL.

### 10.5 Slice 5 — Comparison

**Goal:** overlay polars from two operating conditions or two aircraft; delta tables; CSV export.

**Library files (Stepan):**
- `analysis/comparison.py` — `compare_polars(polar_a, polar_b, alpha_grid=None) -> ComparisonResult`

**Library files (Claude):**
- `viz/plot_utils.py` — `overlay_figure(polars, labels)` for arbitrary number of curves

**App files (Claude):**
- `pages/05_comparison.py` — two pickers, four overlay plots (CL–α, CD–α, L/D–α, CL–CD), Cm overlay if both have manual Cm at matching CGs, delta table at common α, CSV export buttons
- `core/csv_export.py` — write polar set or comparison result to CSV

**Tests added:**
- `test_comparison.py` — known-input comparison
- `test_csv_export.py` — round-trip a known polar through CSV

**Definition of done:** pick two OCs for the same aircraft, see overlaid polars and Δ values at integer α, click "Export CSV," get a file that opens in Excel.

## 11. Testing approach

### 11.1 Discipline

**TDD throughout the library.** Mirrors `dynaprocessing`'s precedent (100+ tests). The five-step rule:

1. Decide what a function should do.
2. Write a test that asserts it.
3. Run the test, watch it fail.
4. Write the minimum implementation to make it pass.
5. Refactor with the test as a safety net.

For Stepan-owned modules this is the chosen learning approach. For Claude-owned modules the same discipline applies so the project keeps one standard.

Streamlit pages are the only exception (§9.5).

### 11.2 Layout

```
libs/aerocfd/tests/
├── conftest.py
├── test_polar.py
├── test_aircraft.py
├── test_operating_condition.py
├── test_alpha_case.py
├── test_dataset.py
├── test_rotation.py
├── test_coefficients.py
├── test_summation.py            # slice 3
├── test_moment_transfer.py      # slice 4
└── test_comparison.py           # slice 5

apps/aerocfd-ui/tests/
├── conftest.py
├── test_database.py
├── test_mappers.py
└── test_csv_export.py           # slice 5
```

One test file per source module — same convention as `dynaprocessing`.

### 11.3 Conventions

- **`pytest`** with default discovery.
- **`pytest.approx`** for float comparisons; explicit `rel=` / `abs=` when default tolerance might mask a real bug.
- **Fixtures in `conftest.py`** for shared test data (e.g. a "reference aircraft" fixture).
- **`@pytest.mark.parametrize`** for the same logic at multiple α values.
- **One assert per test when possible** — failure messages stay readable.
- **No mocking of internal code.** No external dependencies need mocking; if a test needs mocks, the design is wrong.

### 11.4 Coverage

**No formal coverage target.** Real target: every behavior the engineering decisions depend on is asserted somewhere. Gold tests + round-trip mapper tests + per-module behavioral tests cover that without a number.

### 11.5 TDD ownership

- **Stepan writes the assertions** — that is where the engineering decisions live and the learning happens.
- **Claude writes the boilerplate on request** — fixtures, parametrize tables, conftest setup, ORM round-trip scaffolds.
- Both run the tests; pass/fail is the shared source of truth.

## 12. Decisions log

Captured here so future-Stepan can see *why* each choice was made without re-reading the brainstorming exchange.

| Topic | Choice | Reasoning (brief) |
|---|---|---|
| Single-user posture | Warnings, not snapshots | Stepan is the only user; coordination concerns relaxed, correctness concerns kept. |
| DB per app | Yes, separate from `aerisvault-ui` | Anticipates per-tool user separation later. |
| Learning split | Per-module (B) | Stepan writes math/classes, Claude writes scaffolding. |
| Polar shape | Two-layer (Polar + AeroDataset) | Mirrors `Curve` + `InfiniteMassSimulation`; clean unit testing; small first learning piece. |
| Build order | Vertical slice (A) | Earlier learning value, surfaces integration bugs early, forces end-to-end decisions. |
| Slice scope | S2 + Cm | All 2D coefficients from totals, plus Cm at Fluent's reference point. |
| Slice thickness | Streamlit, no DB (C) | Library settles before SQLAlchemy enters; persistence in slice 2. |
| Spec scope | Full v1 roadmap (B) | Detail all 5 slices in this doc. |
| Library structure | Mirror `dynaprocessing` (1) | Pattern-match between libraries; small "empty subpackage" cost is fine. |
| Math library | numpy throughout | Same function works for scalar and array α via broadcasting. |
| Group summation order | Rotate first, sum later | Engineering questions live in wind frame; per-part `(lift, drag)` reads naturally. |
| Cm convention | Sign-flipped via named function | `fluent_my_to_aero` self-documents; gold-test asserts sign for a stable airfoil. |
| Streamlit page testing | Hand-tested in browser, not unit-tested | Glue-only failure modes; library underneath has full coverage. |
| Schema migration in slice 3 | Stepan-written script (or wipe-and-reenter) | Deliberate learning moment about schema evolution. |
| Library naming | `aerocfd` (provisional) | Stepan said *"don't care, can be changed."* Cheap to rename through slice 3. |

## 13. What's next

After Stepan's approval of this spec:

1. Brainstorming skill transitions to `superpowers:writing-plans` to produce an implementation plan for slice 1 (and optionally a roadmap of plans for later slices).
2. `CLAUDE.md` is updated to add an `aerocfd`-specific section: collaboration model, axis convention reminder, key invariants (rotate-first-sum-later, library is ORM-free, etc.) — to be drafted as part of the writing-plans phase.
3. Slice 1 implementation begins with Stepan writing the modules listed in §10.1.

---

*End of design.*
