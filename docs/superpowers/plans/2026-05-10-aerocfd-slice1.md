# aerocfd Slice 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Important — collaboration model.** This is Stepan's learning project. Tasks are tagged **Owner: Stepan** or **Owner: Claude**:
> - **Stepan-owned tasks**: code blocks below are *reference targets*, not handoff drops. The expected workflow is short discussion + Stepan writes + Claude reviews. Do not auto-implement these. The reference code lets Stepan verify behavior and lets a subagent execute if Stepan delegates explicitly.
> - **Claude-owned tasks**: scaffolding/glue. Full implementation is shown and Claude (or a subagent) writes them.
> See `feedback_aerocfd_learning_mode.md` in memory for the per-module split rationale.

**Goal:** Ship a working `aerocfd` library + single-page Streamlit app that takes user-entered totals (Fx, Fz, My in body frame) for a handful of α cases and renders five plots: CL–α, CD–α, L/D–α, CL–CD, Cm–α — all derived from raw loads via body→wind rotation and Cm sign-flip. No database; no parts; no comparison. End-to-end correctness on the smallest possible surface.

**Architecture:** A new analytical library `libs/aerocfd/` (pure Python + numpy + plotly) plus an aerocfd **module inside the `apps/aerisvault/` portal shell** (not a standalone app). The library does all computation; the module is a thin page that delegates to it. Library is ORM-free in v1; the module does not yet touch SQL.

**Tech Stack:** Python 3.10+, numpy, plotly, streamlit, pytest. No SQLAlchemy in slice 1.

**Spec:** [`docs/superpowers/specs/2026-05-10-aerocfd-design.md`](../specs/2026-05-10-aerocfd-design.md) — see §10.1 for slice 1 scope.

> **⚠ AMENDMENT (2026-06-13) — read before executing.** This plan was written before two later decisions; both are now folded into the tasks below:
> 1. **Portal module, not standalone app.** aerocfd's UI is a module in the single `apps/aerisvault/` shell (`apps/aerisvault/src/aerisvault/modules/aerocfd/`), registered via a `ModuleDescriptor`. There is no `apps/aerocfd-ui/`. **Prerequisite:** the portal shell must already exist — built by [`2026-06-13-portal-shell-fsi-migration.md`](2026-06-13-portal-shell-fsi-migration.md). Recommended build order: dynaprocessing refinement → portal+FSI → **aerocfd (this plan)**.
> 2. **Rotation sign fix.** `body_to_wind` is `D = −Fx·cosα + Fz·sinα`, `L = Fx·sinα + Fz·cosα` (Fluent `Fx` is forward-positive; drag points −X). Gold test #1 and a new `CD(α=0)>0` gold test reflect this. The `My` sign flip is unchanged. See [`project_aerocfd_fx_sign_open`] in memory.

---

## File Structure

### `libs/aerocfd/` (NEW)
- `pyproject.toml` — package metadata, dependencies (numpy, plotly), dev (pytest)
- `src/aerocfd/__init__.py` — public re-exports
- `src/aerocfd/models/__init__.py`
- `src/aerocfd/models/polar.py` — `Polar` 1D series indexed by α (Stepan)
- `src/aerocfd/models/aircraft.py` — `Aircraft` frozen dataclass (Stepan)
- `src/aerocfd/models/operating_condition.py` — `OperatingCondition` frozen dataclass (Stepan)
- `src/aerocfd/models/alpha_case.py` — `AlphaCase` frozen dataclass + `ConvergenceStatus` enum (Stepan)
- `src/aerocfd/models/dataset.py` — `AeroDataset` orchestrator (Stepan)
- `src/aerocfd/analysis/__init__.py`
- `src/aerocfd/analysis/rotation.py` — `body_to_wind`, `fluent_my_to_aero` (Stepan)
- `src/aerocfd/analysis/coefficients.py` — `dynamic_pressure`, `cl`, `cd`, `cm`, `lift_to_drag` (Stepan)
- `src/aerocfd/viz/__init__.py`
- `src/aerocfd/viz/plot_utils.py` — five Plotly figure helpers (Claude)
- `src/aerocfd/io/__init__.py` — empty in v1
- `tests/conftest.py` — shared fixtures (Claude scaffolds, Stepan extends)
- `tests/test_polar.py`, `tests/test_aircraft.py`, `tests/test_operating_condition.py`, `tests/test_alpha_case.py`, `tests/test_dataset.py`, `tests/test_rotation.py`, `tests/test_coefficients.py`, `tests/test_plot_utils.py`

### aerocfd module inside the portal shell (NEW)
- `apps/aerisvault/src/aerisvault/modules/aerocfd/__init__.py` — exposes the `ModuleDescriptor` (Claude)
- `apps/aerisvault/src/aerisvault/modules/aerocfd/pages/__init__.py`
- `apps/aerisvault/src/aerisvault/modules/aerocfd/pages/polar.py` — single page with `render()` (Claude)
- `apps/aerisvault/src/aerisvault/portal/registry.py` — one line added to register the module (Claude)
- No `apps/aerocfd-ui/` and no extra `pyproject.toml`: the module lives inside the existing `aerisvault` package.

### Repo root
- `CLAUDE.md` — appended with an `aerocfd`-specific section (Claude drafts, Stepan reviews)
- `pyproject.toml` (root) — version unchanged for slice 1; no edit needed unless the version-bump rule is exercised this slice
- `data/aerocfd/` — directory created in slice 2; not needed here

---

## Task 1: Package skeletons & install

**Owner:** Claude

**Files:**
- Create: `libs/aerocfd/pyproject.toml`
- Create: `libs/aerocfd/src/aerocfd/__init__.py`
- Create: `libs/aerocfd/src/aerocfd/models/__init__.py`
- Create: `libs/aerocfd/src/aerocfd/analysis/__init__.py`
- Create: `libs/aerocfd/src/aerocfd/viz/__init__.py`
- Create: `libs/aerocfd/src/aerocfd/io/__init__.py`
- Create: `libs/aerocfd/tests/__init__.py`
- Create: `apps/aerisvault/src/aerisvault/modules/aerocfd/__init__.py` (filled in Task 10)
- Create: `apps/aerisvault/src/aerisvault/modules/aerocfd/pages/__init__.py`

- [ ] **Step 1: Create `libs/aerocfd/pyproject.toml`**

```toml
[project]
name = "aerocfd"
version = "0.1.0"
description = "Aircraft CFD post-processing library for AerisVault"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "numpy>=1.24",
    "plotly>=5.15",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-cov>=4.0"]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
include = ["aerocfd*"]
```

- [ ] **Step 2: Create empty `__init__.py` files**

All five `__init__.py` files (top-level package + `models/`, `analysis/`, `viz/`, `io/`, `tests/`) are empty for now. Public re-exports in the top-level `aerocfd/__init__.py` are added incrementally as types appear.

- [ ] **Step 3: Create the aerocfd module package dirs inside the shell**

The aerocfd UI is a module in the already-existing `apps/aerisvault/` shell — no separate app, no extra `pyproject.toml`. Create the package markers:

```bash
cd /home/stepan/projects/PhD/AerisVault/apps/aerisvault/src/aerisvault
mkdir -p modules/aerocfd/pages
touch modules/aerocfd/__init__.py modules/aerocfd/pages/__init__.py
```

(`modules/aerocfd/__init__.py` stays empty until Task 10, when its `ModuleDescriptor` is added.)

- [ ] **Step 4: Install the aerocfd library editable**

The `aerisvault` shell is already installed (from the portal+FSI migration). Only the new library needs installing:

```bash
/home/stepan/projects/PhD/AerisVault/.venv/bin/pip install -e libs/aerocfd
```

Expected: finishes with `Successfully installed aerocfd-0.1.0`.

- [ ] **Step 5: Smoke import**

Run:
```bash
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -c "import aerocfd; import aerisvault.modules.aerocfd; print('ok')"
```

Expected: `ok`.

- [ ] **Step 6: Commit**

```bash
git add libs/aerocfd apps/aerisvault/src/aerisvault/modules/aerocfd
git commit -m "scaffold: aerocfd library and aerocfd module skeleton"
```

---

## Task 2: Test scaffolding (`conftest.py` with starter fixtures)

**Owner:** Claude (Stepan extends as needed)

**Files:**
- Create: `libs/aerocfd/tests/conftest.py`

- [ ] **Step 1: Create `libs/aerocfd/tests/conftest.py`**

```python
"""Shared fixtures for the aerocfd test suite."""
import numpy as np
import pytest


@pytest.fixture
def alpha_grid_deg():
    """Five α values spanning a typical small-angle sweep."""
    return np.array([-5.0, 0.0, 5.0, 10.0, 15.0])


@pytest.fixture
def reference_aircraft_kwargs():
    """Reasonable defaults for a small fixed-wing reference aircraft."""
    return dict(
        name="Reference",
        s_ref_m2=10.0,
        c_ref_m=1.5,
        b_ref_m=8.0,
    )


@pytest.fixture
def reference_operating_condition_kwargs():
    """Sea-level standard atmosphere, 50 m/s."""
    return dict(
        name="SL_50mps",
        velocity_mps=50.0,
        density_kgpm3=1.225,
    )
```

- [ ] **Step 2: Verify pytest discovers the file**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest --collect-only
```

Expected: `no tests ran` (no test files yet) but no errors during collection.

- [ ] **Step 3: Commit**

```bash
git add libs/aerocfd/tests/conftest.py
git commit -m "test: add conftest with shared aerocfd fixtures"
```

---

## Task 3: `Polar` class

**Owner:** Stepan (collaborative — Claude reviews, helps with edge cases)

**Files:**
- Create: `libs/aerocfd/src/aerocfd/models/polar.py`
- Create: `libs/aerocfd/tests/test_polar.py`

**Note:** the code blocks below are *reference targets*, not auto-handoff. Discuss before writing; Stepan writes; Claude reviews.

- [ ] **Step 1: Write the failing tests**

Reference target for `tests/test_polar.py`:

```python
import numpy as np
import pytest

from aerocfd.models.polar import Polar


class TestPolarConstruction:
    def test_construct_with_arrays(self, alpha_grid_deg):
        values = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        polar = Polar(alpha_deg=alpha_grid_deg, values=values, name="CL", units="-")
        assert polar.name == "CL"
        assert polar.units == "-"

    def test_alpha_and_values_are_arrays(self, alpha_grid_deg):
        polar = Polar(alpha_deg=alpha_grid_deg, values=np.zeros(5), name="dummy")
        assert isinstance(polar.alpha_deg, np.ndarray)
        assert isinstance(polar.values, np.ndarray)
        assert polar.alpha_deg.shape == polar.values.shape

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            Polar(alpha_deg=np.array([0.0, 5.0]), values=np.array([1.0]), name="bad")


class TestPolarInterpolation:
    def test_interpolate_at_known_point(self, alpha_grid_deg):
        # values increase linearly from 0 to 1 across α=-5..15
        values = np.linspace(0.0, 1.0, 5)
        polar = Polar(alpha_deg=alpha_grid_deg, values=values, name="linear")
        # midpoint α=5 must be 0.5 (the center of a 5-point linear ramp)
        assert polar.interpolate_at(5.0) == pytest.approx(0.5)

    def test_interpolate_outside_range_clips(self, alpha_grid_deg):
        # numpy.interp clips at the edges (no extrapolation). Lock that behavior.
        values = np.linspace(0.0, 1.0, 5)
        polar = Polar(alpha_deg=alpha_grid_deg, values=values, name="linear")
        assert polar.interpolate_at(-100.0) == pytest.approx(0.0)   # below alpha range
        assert polar.interpolate_at(100.0) == pytest.approx(1.0)    # above alpha range


class TestPolarSlicing:
    def test_slice_alpha_returns_subset(self, alpha_grid_deg):
        values = np.linspace(0.0, 1.0, 5)
        polar = Polar(alpha_deg=alpha_grid_deg, values=values, name="x")
        sub = polar.slice_alpha(0.0, 10.0)
        assert sub.alpha_deg.tolist() == [0.0, 5.0, 10.0]
        assert sub.values.tolist() == pytest.approx([0.25, 0.5, 0.75])
```

**Discussion point** (before writing): out-of-range interpolation behavior. Recommended default: use `numpy.interp` which clips at boundaries. Document the choice in the docstring.

- [ ] **Step 2: Run tests, verify failure**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_polar.py -v
```

Expected: collection error or `ImportError: aerocfd.models.polar` — confirms the module doesn't exist yet.

- [ ] **Step 3: Implement `Polar`**

Reference target for `src/aerocfd/models/polar.py`:

```python
"""Polar — a 1D ordered series indexed by angle of attack."""
from __future__ import annotations

import numpy as np


class Polar:
    """1D ordered series indexed by angle of attack.

    Polar is the aerocfd analogue of dynaprocessing's Curve, with α as the
    independent variable instead of time. Immutable by convention: methods
    that transform a Polar return a new instance.
    """

    def __init__(
        self,
        alpha_deg: np.ndarray,
        values: np.ndarray,
        name: str = "Unknown",
        units: str | None = None,
        metadata: dict | None = None,
    ):
        alpha_deg = np.asarray(alpha_deg, dtype=float)
        values = np.asarray(values, dtype=float)
        if alpha_deg.shape != values.shape:
            raise ValueError(
                f"alpha_deg shape {alpha_deg.shape} != values shape {values.shape}"
            )
        # Sort by alpha so interpolate_at and slice_alpha can rely on monotonic input.
        order = np.argsort(alpha_deg)
        self._alpha_deg = alpha_deg[order]
        self._values = values[order]
        self.name = name
        self.units = units
        self.metadata = dict(metadata) if metadata else {}

    @property
    def alpha_deg(self) -> np.ndarray:
        return self._alpha_deg

    @property
    def values(self) -> np.ndarray:
        return self._values

    def interpolate_at(self, alpha_deg: float) -> float:
        """Linear interpolation. Clips at the polar's α range (numpy.interp default)."""
        return float(np.interp(alpha_deg, self._alpha_deg, self._values))

    def slice_alpha(self, alpha_min: float, alpha_max: float) -> "Polar":
        """Return a new Polar containing only points with α ∈ [alpha_min, alpha_max]."""
        mask = (self._alpha_deg >= alpha_min) & (self._alpha_deg <= alpha_max)
        return Polar(
            alpha_deg=self._alpha_deg[mask],
            values=self._values[mask],
            name=self.name,
            units=self.units,
            metadata=self.metadata,
        )
```

- [ ] **Step 4: Run tests, verify passing**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_polar.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add libs/aerocfd/src/aerocfd/models/polar.py libs/aerocfd/tests/test_polar.py
git commit -m "feat(aerocfd): add Polar 1D series indexed by alpha"
```

---

## Task 4: Plain dataclasses (`Aircraft`, `OperatingCondition`, `ConvergenceStatus`, `AlphaCase`)

**Owner:** Stepan (collaborative)

**Files:**
- Create: `libs/aerocfd/src/aerocfd/models/aircraft.py`
- Create: `libs/aerocfd/src/aerocfd/models/operating_condition.py`
- Create: `libs/aerocfd/src/aerocfd/models/alpha_case.py`
- Create: `libs/aerocfd/tests/test_aircraft.py`
- Create: `libs/aerocfd/tests/test_operating_condition.py`
- Create: `libs/aerocfd/tests/test_alpha_case.py`

- [ ] **Step 1: Write `tests/test_aircraft.py`**

Reference target:

```python
import pytest
from dataclasses import FrozenInstanceError

from aerocfd.models.aircraft import Aircraft


class TestAircraft:
    def test_construct_with_required_fields(self, reference_aircraft_kwargs):
        ac = Aircraft(**reference_aircraft_kwargs)
        assert ac.name == "Reference"
        assert ac.s_ref_m2 == pytest.approx(10.0)
        assert ac.axis_convention == "x_fwd_z_up_rh"

    def test_is_frozen(self, reference_aircraft_kwargs):
        ac = Aircraft(**reference_aircraft_kwargs)
        with pytest.raises(FrozenInstanceError):
            ac.s_ref_m2 = 20.0
```

- [ ] **Step 2: Write `tests/test_operating_condition.py`**

Reference target:

```python
import pytest
from dataclasses import FrozenInstanceError

from aerocfd.models.operating_condition import OperatingCondition


class TestOperatingCondition:
    def test_construct(self, reference_operating_condition_kwargs):
        oc = OperatingCondition(**reference_operating_condition_kwargs)
        assert oc.name == "SL_50mps"
        assert oc.velocity_mps == pytest.approx(50.0)
        assert oc.density_kgpm3 == pytest.approx(1.225)

    def test_is_frozen(self, reference_operating_condition_kwargs):
        oc = OperatingCondition(**reference_operating_condition_kwargs)
        with pytest.raises(FrozenInstanceError):
            oc.velocity_mps = 80.0
```

- [ ] **Step 3: Write `tests/test_alpha_case.py`**

Reference target:

```python
import pytest
from dataclasses import FrozenInstanceError

from aerocfd.models.alpha_case import AlphaCase, ConvergenceStatus


class TestConvergenceStatus:
    def test_has_expected_members(self):
        names = {s.name for s in ConvergenceStatus}
        assert names == {
            "CONVERGED", "PARTIALLY_CONVERGED", "OSCILLATING",
            "DIVERGED", "STOPPED_MANUALLY", "UNKNOWN",
        }


class TestAlphaCase:
    def test_construct_minimal(self):
        case = AlphaCase(alpha_deg=5.0, fx_n=-100.0, fz_n=1000.0, my_nm=50.0)
        assert case.alpha_deg == pytest.approx(5.0)
        assert case.convergence_status == ConvergenceStatus.UNKNOWN

    def test_is_frozen(self):
        case = AlphaCase(alpha_deg=5.0, fx_n=0.0, fz_n=0.0, my_nm=0.0)
        with pytest.raises(FrozenInstanceError):
            case.alpha_deg = 10.0
```

- [ ] **Step 4: Run tests, verify failure**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_aircraft.py tests/test_operating_condition.py tests/test_alpha_case.py -v
```

Expected: import errors for all three modules.

- [ ] **Step 5: Implement `aircraft.py`**

```python
"""Aircraft reference values and identity."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Aircraft:
    """Reference values for one aircraft.

    All references are SI: areas in m², lengths in m. The axis convention
    string is the contract that downstream rotation/sign-flip code relies on.
    """
    name: str
    s_ref_m2: float
    c_ref_m: float
    b_ref_m: float
    axis_convention: str = "x_fwd_z_up_rh"
    description: str = ""
```

- [ ] **Step 6: Implement `operating_condition.py`**

```python
"""Operating condition (one Fluent setup, varying α)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperatingCondition:
    """Free-stream conditions for one fixed Fluent setup."""
    name: str
    velocity_mps: float
    density_kgpm3: float
    description: str = ""
```

- [ ] **Step 7: Implement `alpha_case.py`**

```python
"""Per-α data for one operating condition (slice 1: totals only)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConvergenceStatus(str, Enum):
    CONVERGED = "converged"
    PARTIALLY_CONVERGED = "partially_converged"
    OSCILLATING = "oscillating"
    DIVERGED = "diverged"
    STOPPED_MANUALLY = "stopped_manually"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AlphaCase:
    """One Fluent run at a fixed α.

    Forces and moments are TOTALS in the body frame, exactly as Fluent reports
    them. The library does the body→wind rotation and the My sign flip; storage
    keeps the raw values.
    """
    alpha_deg: float
    fx_n: float
    fz_n: float
    my_nm: float
    convergence_status: ConvergenceStatus = ConvergenceStatus.UNKNOWN
    notes: str = ""
```

- [ ] **Step 8: Run tests, verify passing**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_aircraft.py tests/test_operating_condition.py tests/test_alpha_case.py -v
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add libs/aerocfd/src/aerocfd/models/aircraft.py libs/aerocfd/src/aerocfd/models/operating_condition.py libs/aerocfd/src/aerocfd/models/alpha_case.py libs/aerocfd/tests/test_aircraft.py libs/aerocfd/tests/test_operating_condition.py libs/aerocfd/tests/test_alpha_case.py
git commit -m "feat(aerocfd): add Aircraft, OperatingCondition, AlphaCase, ConvergenceStatus"
```

---

## Task 5: `rotation.py` — body→wind & Cm sign flip (the gold tests)

**Owner:** Stepan (collaborative — these are the spine of the library)

**Files:**
- Create: `libs/aerocfd/src/aerocfd/analysis/rotation.py`
- Create: `libs/aerocfd/tests/test_rotation.py`

**Why this is critical:** these two functions encode the axis convention (see `project_aerocfd_axis_convention.md` in memory). Every stored polar depends on them. Convention change ≡ breaking schema change.

- [ ] **Step 1: Write `tests/test_rotation.py` with rotation gold tests #1 and #2 (plus the My sign-flip tests)**

(Gold test #3, the stable-airfoil Cm sign-flip, and #4, `CD(α=0)>0`, live in `tests/test_dataset.py` — Task 7 — since they need `AeroDataset`.)

Reference target:

```python
import numpy as np
import pytest

from aerocfd.analysis.rotation import body_to_wind, fluent_my_to_aero


class TestBodyToWindGoldStandards:
    """Rotation gold tests #1 and #2. If these ever fail, the convention is broken."""

    def test_zero_alpha_drag_lift(self):
        # Fluent Fx is forward-positive; drag points -X. At α=0 the body and
        # wind axes align, so drag = -Fx (positive for a draggy body, Fx<0)
        # and lift = +Fz. With Fx=-100 (a drag force of 100 N), drag = +100.
        drag, lift = body_to_wind(fx_n=-100.0, fz_n=1000.0, alpha_deg=0.0)
        assert drag == pytest.approx(100.0)
        assert lift == pytest.approx(1000.0)

    def test_pure_vertical_force_at_10_deg(self):
        # Pure +Fz of 1000 N at α=10°:
        # drag = 0·cos(10°) + 1000·sin(10°) = +173.6 N
        # lift = -0·sin(10°) + 1000·cos(10°) = +984.8 N
        drag, lift = body_to_wind(fx_n=0.0, fz_n=1000.0, alpha_deg=10.0)
        assert drag == pytest.approx(1000.0 * np.sin(np.radians(10.0)))
        assert lift == pytest.approx(1000.0 * np.cos(np.radians(10.0)))

    def test_array_broadcasting(self):
        fx = np.array([0.0, 0.0, 0.0])
        fz = np.array([1000.0, 1000.0, 1000.0])
        alpha = np.array([0.0, 10.0, 20.0])
        drag, lift = body_to_wind(fx, fz, alpha)
        assert drag.shape == (3,)
        assert lift.shape == (3,)
        assert drag[0] == pytest.approx(0.0)
        assert lift[0] == pytest.approx(1000.0)


class TestFluentMyToAero:
    def test_sign_is_flipped(self):
        # Fluent's right-hand-rule My, with y pointing left, is nose-DOWN positive.
        # Aerospace Cm is nose-UP positive. So the conversion is a sign flip.
        assert fluent_my_to_aero(50.0) == pytest.approx(-50.0)
        assert fluent_my_to_aero(-30.0) == pytest.approx(30.0)

    def test_array_input(self):
        my_fluent = np.array([10.0, -20.0, 0.0])
        result = fluent_my_to_aero(my_fluent)
        assert np.allclose(result, np.array([-10.0, 20.0, 0.0]))
```

- [ ] **Step 2: Run tests, verify failure**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_rotation.py -v
```

Expected: `ModuleNotFoundError: aerocfd.analysis.rotation`.

- [ ] **Step 3: Implement `rotation.py`**

Reference target:

```python
"""Body↔wind rotation and Cm sign convention.

Axis convention (the contract):
- Body frame: x = forward, z = up, right-handed → y points to the left.
- α positive = nose up.
- Fluent reports loads in this fixed body frame regardless of α.
- Sideslip is ignored in v1 (β = 0); rotation stays in the x–z plane.
"""
from __future__ import annotations

import numpy as np


def body_to_wind(fx_n, fz_n, alpha_deg):
    """Rotate body-frame total force (force ON the body, x forward, z up)
    to wind frame. Returns (drag_n, lift_n). Scalars or numpy arrays.

    Fluent's Fx is forward-positive, so the drag-producing axial force is
    negative — hence the minus sign on the Fx drag term:

        drag = -Fx·cos(α) + Fz·sin(α)
        lift =  Fx·sin(α) + Fz·cos(α)

    At α=0: drag = -Fx (positive for a draggy body), lift = Fz.
    """
    alpha_rad = np.radians(alpha_deg)
    cos_a = np.cos(alpha_rad)
    sin_a = np.sin(alpha_rad)
    drag_n = -fx_n * cos_a + fz_n * sin_a
    lift_n =  fx_n * sin_a + fz_n * cos_a
    return drag_n, lift_n


def fluent_my_to_aero(my_fluent_nm):
    """Flip the sign of Fluent's My to match aerospace Cm convention.

    With body y pointing left, Fluent's right-hand-rule My is nose-DOWN positive.
    Aerospace Cm convention is nose-UP positive. So:
        My_aero = -My_fluent
    """
    return -my_fluent_nm
```

- [ ] **Step 4: Run tests, verify passing**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_rotation.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add libs/aerocfd/src/aerocfd/analysis/rotation.py libs/aerocfd/tests/test_rotation.py
git commit -m "feat(aerocfd): add body_to_wind rotation and fluent_my_to_aero sign flip with gold tests"
```

---

## Task 6: `coefficients.py`

**Owner:** Stepan (collaborative)

**Files:**
- Create: `libs/aerocfd/src/aerocfd/analysis/coefficients.py`
- Create: `libs/aerocfd/tests/test_coefficients.py`

- [ ] **Step 1: Write `tests/test_coefficients.py`**

Reference target:

```python
import numpy as np
import pytest

from aerocfd.analysis.coefficients import (
    dynamic_pressure, cl, cd, cm, lift_to_drag,
)


class TestDynamicPressure:
    def test_known_value(self):
        # q = 0.5 · 1.225 · 50² = 1531.25 Pa
        assert dynamic_pressure(1.225, 50.0) == pytest.approx(1531.25)

    def test_array_velocity(self):
        v = np.array([10.0, 50.0, 100.0])
        q = dynamic_pressure(1.225, v)
        assert np.allclose(q, 0.5 * 1.225 * v**2)


class TestCoefficients:
    def test_cl_known_value(self):
        # CL = lift / (q · S_ref) = 1000 / (1531.25 · 10) = 0.0653...
        assert cl(1000.0, 1531.25, 10.0) == pytest.approx(1000.0 / 15312.5)

    def test_cd_known_value(self):
        assert cd(100.0, 1531.25, 10.0) == pytest.approx(100.0 / 15312.5)

    def test_cm_known_value(self):
        # Cm = My_aero / (q · S_ref · c_ref)
        assert cm(50.0, 1531.25, 10.0, 1.5) == pytest.approx(50.0 / (1531.25 * 10.0 * 1.5))


class TestLiftToDrag:
    def test_simple_ratio(self):
        assert lift_to_drag(1000.0, 100.0) == pytest.approx(10.0)

    def test_zero_drag_returns_inf(self):
        result = lift_to_drag(1000.0, 0.0)
        assert np.isinf(result)

    def test_array_input(self):
        lift = np.array([1000.0, 1000.0])
        drag = np.array([100.0, 200.0])
        assert np.allclose(lift_to_drag(lift, drag), [10.0, 5.0])
```

- [ ] **Step 2: Run tests, verify failure**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_coefficients.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `coefficients.py`**

Reference target:

```python
"""Aerodynamic coefficient definitions (SI throughout)."""
from __future__ import annotations

import numpy as np


def dynamic_pressure(density_kgpm3, velocity_mps):
    """q∞ = ½ρV²."""
    return 0.5 * density_kgpm3 * velocity_mps**2


def cl(lift_n, q_pa, s_ref_m2):
    return lift_n / (q_pa * s_ref_m2)


def cd(drag_n, q_pa, s_ref_m2):
    return drag_n / (q_pa * s_ref_m2)


def cm(my_aero_nm, q_pa, s_ref_m2, c_ref_m):
    """Pitching-moment coefficient. Caller must pass My already in aerospace
    convention (i.e. after fluent_my_to_aero)."""
    return my_aero_nm / (q_pa * s_ref_m2 * c_ref_m)


def lift_to_drag(lift_n, drag_n):
    """L/D, element-wise. Drag = 0 → +∞ (or −∞ if lift is negative)."""
    drag_arr = np.asarray(drag_n, dtype=float)
    lift_arr = np.asarray(lift_n, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.where(drag_arr == 0.0, np.sign(lift_arr) * np.inf, lift_arr / drag_arr)
    if result.ndim == 0:
        return float(result)
    return result
```

- [ ] **Step 4: Run tests, verify passing**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_coefficients.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add libs/aerocfd/src/aerocfd/analysis/coefficients.py libs/aerocfd/tests/test_coefficients.py
git commit -m "feat(aerocfd): add aerodynamic coefficient functions"
```

---

## Task 7: `AeroDataset` orchestrator + gold tests #3 and #4

**Owner:** Stepan (collaborative — Claude can scaffold the fixture)

**Files:**
- Create: `libs/aerocfd/src/aerocfd/models/dataset.py`
- Create: `libs/aerocfd/tests/test_dataset.py`
- Modify: `libs/aerocfd/tests/conftest.py` (add a `stable_airfoil_dataset` fixture)

- [ ] **Step 1: Add fixture to `conftest.py`**

Append to `libs/aerocfd/tests/conftest.py`:

```python
@pytest.fixture
def stable_airfoil_alpha_cases():
    """Synthetic α sweep that mimics a stable airfoil:
    - lift increases ~linearly with α
    - drag is small and roughly parabolic
    - Fluent My is positive for positive α (nose-DOWN in this convention),
      so after the sign flip Cm should be negative for positive α — the
      hallmark of a longitudinally stable configuration.
    """
    from aerocfd.models.alpha_case import AlphaCase
    cases = []
    for alpha in [-5.0, 0.0, 5.0, 10.0, 15.0]:
        # body-frame totals
        fz = 100.0 * alpha + 200.0       # rough lift slope, body frame
        fx = -10.0 - 0.5 * alpha**2      # small drag (negative = backward)
        my_fluent = 5.0 * alpha          # nose-down positive in this convention
        cases.append(AlphaCase(alpha_deg=alpha, fx_n=fx, fz_n=fz, my_nm=my_fluent))
    return cases
```

- [ ] **Step 2: Write `tests/test_dataset.py`**

Reference target:

```python
import numpy as np
import pytest

from aerocfd.models.aircraft import Aircraft
from aerocfd.models.operating_condition import OperatingCondition
from aerocfd.models.dataset import AeroDataset
from aerocfd.models.polar import Polar


@pytest.fixture
def reference_dataset(reference_aircraft_kwargs, reference_operating_condition_kwargs,
                      stable_airfoil_alpha_cases):
    aircraft = Aircraft(**reference_aircraft_kwargs)
    oc = OperatingCondition(**reference_operating_condition_kwargs)
    return AeroDataset(aircraft=aircraft, operating_condition=oc,
                       alpha_cases=stable_airfoil_alpha_cases)


class TestAeroDatasetBasics:
    def test_alpha_deg_is_sorted_array(self, reference_dataset):
        alpha = reference_dataset.alpha_deg
        assert isinstance(alpha, np.ndarray)
        assert np.all(np.diff(alpha) > 0)

    def test_dynamic_pressure(self, reference_dataset):
        # q = 0.5 · 1.225 · 50² = 1531.25 Pa
        assert reference_dataset.dynamic_pressure_pa == pytest.approx(1531.25)


class TestAeroDatasetPolars:
    def test_lift_is_polar(self, reference_dataset):
        assert isinstance(reference_dataset.lift(), Polar)

    def test_cl_is_dimensionless(self, reference_dataset):
        polar = reference_dataset.cl()
        assert polar.units == "-"

    def test_lift_to_drag_at_zero_alpha_matches_lift_over_drag(self, reference_dataset):
        ld = reference_dataset.lift_to_drag()
        lift = reference_dataset.lift()
        drag = reference_dataset.drag()
        idx = np.where(reference_dataset.alpha_deg == 0.0)[0][0]
        assert ld.values[idx] == pytest.approx(lift.values[idx] / drag.values[idx])


class TestStableAirfoilGoldStandard:
    """Gold test #3: Cm sign-flip regression — Cm negative for positive α
    on the synthetic stable airfoil (My_fluent = 5·α by construction, so this
    can only fail if the fluent_my_to_aero sign flip is dropped)."""

    def test_cm_is_negative_at_positive_alpha(self, reference_dataset):
        cm_polar = reference_dataset.cm()
        for alpha, cm_value in zip(cm_polar.alpha_deg, cm_polar.values):
            if alpha > 0:
                assert cm_value < 0, (
                    f"Cm sign-flip regression failed at α={alpha}°: Cm={cm_value} "
                    "should be negative (nose-down). Sign flip likely missing."
                )


class TestPositiveDragGoldStandard:
    """Gold test #4: CD at α=0 must be strictly positive for a draggy aircraft.

    This is the invariant that catches an Fx-sign error in body_to_wind —
    gold test #2 (Fx=0) cannot, because its Fx term vanishes. The sample
    fixture uses negative fx_n (Fluent reports drag as a -X force on the body),
    so a correct rotation yields positive CD at α=0.
    """

    def test_cd_is_positive_at_zero_alpha(self, reference_dataset):
        cd_polar = reference_dataset.cd()
        idx = int(np.where(cd_polar.alpha_deg == 0.0)[0][0])
        assert cd_polar.values[idx] > 0.0, (
            f"CD(α=0) = {cd_polar.values[idx]} must be > 0. A non-positive value "
            "means the body→wind Fx sign is wrong."
        )
```

- [ ] **Step 3: Run tests, verify failure**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_dataset.py -v
```

Expected: `ModuleNotFoundError: aerocfd.models.dataset`.

- [ ] **Step 4: Implement `models/dataset.py`**

Reference target:

```python
"""AeroDataset — orchestrates Polars from raw α-case loads."""
from __future__ import annotations

import numpy as np

from aerocfd.analysis.coefficients import (
    dynamic_pressure, cl, cd, cm, lift_to_drag,
)
from aerocfd.analysis.rotation import body_to_wind, fluent_my_to_aero
from aerocfd.models.aircraft import Aircraft
from aerocfd.models.alpha_case import AlphaCase
from aerocfd.models.operating_condition import OperatingCondition
from aerocfd.models.polar import Polar


class AeroDataset:
    """Aerodynamic dataset for one operating condition.

    Holds raw body-frame loads + references; derives Polars on demand.
    Cases are sorted by α at construction.
    """

    def __init__(
        self,
        aircraft: Aircraft,
        operating_condition: OperatingCondition,
        alpha_cases: list[AlphaCase],
    ):
        self.aircraft = aircraft
        self.operating_condition = operating_condition
        self._cases = sorted(alpha_cases, key=lambda c: c.alpha_deg)

    @property
    def alpha_deg(self) -> np.ndarray:
        return np.array([c.alpha_deg for c in self._cases], dtype=float)

    @property
    def fx_body_n(self) -> np.ndarray:
        return np.array([c.fx_n for c in self._cases], dtype=float)

    @property
    def fz_body_n(self) -> np.ndarray:
        return np.array([c.fz_n for c in self._cases], dtype=float)

    @property
    def my_fluent_nm(self) -> np.ndarray:
        return np.array([c.my_nm for c in self._cases], dtype=float)

    @property
    def dynamic_pressure_pa(self) -> float:
        return dynamic_pressure(
            self.operating_condition.density_kgpm3,
            self.operating_condition.velocity_mps,
        )

    def drag(self) -> Polar:
        drag_n, _ = body_to_wind(self.fx_body_n, self.fz_body_n, self.alpha_deg)
        return Polar(self.alpha_deg, drag_n, name="Drag", units="N")

    def lift(self) -> Polar:
        _, lift_n = body_to_wind(self.fx_body_n, self.fz_body_n, self.alpha_deg)
        return Polar(self.alpha_deg, lift_n, name="Lift", units="N")

    def cl(self) -> Polar:
        values = cl(self.lift().values, self.dynamic_pressure_pa,
                    self.aircraft.s_ref_m2)
        return Polar(self.alpha_deg, values, name="CL", units="-")

    def cd(self) -> Polar:
        values = cd(self.drag().values, self.dynamic_pressure_pa,
                    self.aircraft.s_ref_m2)
        return Polar(self.alpha_deg, values, name="CD", units="-")

    def lift_to_drag(self) -> Polar:
        values = lift_to_drag(self.lift().values, self.drag().values)
        return Polar(self.alpha_deg, values, name="L/D", units="-")

    def cm(self) -> Polar:
        my_aero = fluent_my_to_aero(self.my_fluent_nm)
        values = cm(my_aero, self.dynamic_pressure_pa,
                    self.aircraft.s_ref_m2, self.aircraft.c_ref_m)
        return Polar(self.alpha_deg, values, name="Cm", units="-")
```

- [ ] **Step 5: Run tests, verify passing**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_dataset.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Run the full library test suite**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -v
```

Expected: all tests across `test_polar.py`, `test_aircraft.py`, `test_operating_condition.py`, `test_alpha_case.py`, `test_rotation.py`, `test_coefficients.py`, `test_dataset.py` pass.

- [ ] **Step 7: Commit**

```bash
git add libs/aerocfd/src/aerocfd/models/dataset.py libs/aerocfd/tests/test_dataset.py libs/aerocfd/tests/conftest.py
git commit -m "feat(aerocfd): add AeroDataset orchestrator with stable-airfoil and positive-drag gold tests"
```

---

## Task 8: `viz/plot_utils.py` — five Plotly figure helpers

**Owner:** Claude

**Files:**
- Create: `libs/aerocfd/src/aerocfd/viz/plot_utils.py`
- Create: `libs/aerocfd/tests/test_plot_utils.py`

- [ ] **Step 1: Write `tests/test_plot_utils.py`**

```python
import numpy as np
import pytest
import plotly.graph_objects as go

from aerocfd.models.polar import Polar
from aerocfd.viz.plot_utils import (
    cl_alpha_figure, cd_alpha_figure, lift_to_drag_alpha_figure,
    drag_polar_figure, cm_alpha_figure,
)


@pytest.fixture
def cl_polar():
    return Polar(np.array([-5.0, 0.0, 5.0, 10.0]),
                 np.array([-0.3, 0.0, 0.5, 1.0]), name="CL", units="-")


@pytest.fixture
def cd_polar():
    return Polar(np.array([-5.0, 0.0, 5.0, 10.0]),
                 np.array([0.05, 0.02, 0.04, 0.10]), name="CD", units="-")


class TestFigureHelpers:
    def test_cl_alpha_returns_figure(self, cl_polar):
        fig = cl_alpha_figure(cl_polar)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1

    def test_cd_alpha_returns_figure(self, cd_polar):
        assert isinstance(cd_alpha_figure(cd_polar), go.Figure)

    def test_lift_to_drag_returns_figure(self, cl_polar):
        # Reuse cl_polar shape just for L/D values; not physically meaningful here.
        ld = Polar(cl_polar.alpha_deg, np.array([0.0, 5.0, 12.0, 10.0]),
                   name="L/D", units="-")
        assert isinstance(lift_to_drag_alpha_figure(ld), go.Figure)

    def test_drag_polar_returns_figure(self, cl_polar, cd_polar):
        fig = drag_polar_figure(cl_polar, cd_polar)
        assert isinstance(fig, go.Figure)
        # x = CD, y = CL on a drag polar
        assert fig.layout.xaxis.title.text and "CD" in fig.layout.xaxis.title.text
        assert fig.layout.yaxis.title.text and "CL" in fig.layout.yaxis.title.text

    def test_cm_alpha_returns_figure(self, cl_polar):
        cm = Polar(cl_polar.alpha_deg, np.array([0.05, 0.0, -0.05, -0.1]),
                   name="Cm", units="-")
        assert isinstance(cm_alpha_figure(cm), go.Figure)
```

- [ ] **Step 2: Run tests, verify failure**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_plot_utils.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `viz/plot_utils.py`**

```python
"""Plotly figure helpers — one function per figure used by the UI.

The library returns Figure objects; the UI passes them straight to
st.plotly_chart. UI never builds plots itself.
"""
from __future__ import annotations

import plotly.graph_objects as go

from aerocfd.models.polar import Polar


def _alpha_y_figure(polar: Polar, y_label: str, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=polar.alpha_deg, y=polar.values, mode="lines+markers", name=polar.name,
    ))
    fig.update_layout(
        title=title,
        xaxis_title="α [deg]",
        yaxis_title=y_label,
    )
    return fig


def cl_alpha_figure(cl_polar: Polar) -> go.Figure:
    return _alpha_y_figure(cl_polar, "CL [-]", "Lift coefficient vs α")


def cd_alpha_figure(cd_polar: Polar) -> go.Figure:
    return _alpha_y_figure(cd_polar, "CD [-]", "Drag coefficient vs α")


def lift_to_drag_alpha_figure(ld_polar: Polar) -> go.Figure:
    return _alpha_y_figure(ld_polar, "L/D [-]", "Lift-to-drag ratio vs α")


def cm_alpha_figure(cm_polar: Polar) -> go.Figure:
    return _alpha_y_figure(cm_polar, "Cm [-]", "Pitching-moment coefficient vs α")


def drag_polar_figure(cl_polar: Polar, cd_polar: Polar) -> go.Figure:
    """Drag polar: CL on Y, CD on X."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cd_polar.values, y=cl_polar.values, mode="lines+markers", name="CL–CD",
    ))
    fig.update_layout(
        title="Drag polar (CL vs CD)",
        xaxis_title="CD [-]",
        yaxis_title="CL [-]",
    )
    return fig
```

- [ ] **Step 4: Run tests, verify passing**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_plot_utils.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add libs/aerocfd/src/aerocfd/viz/plot_utils.py libs/aerocfd/tests/test_plot_utils.py
git commit -m "feat(aerocfd): add Plotly figure helpers for the five slice-1 plots"
```

---

## Task 9: Top-level public re-exports

**Owner:** Claude

**Files:**
- Modify: `libs/aerocfd/src/aerocfd/__init__.py`

- [ ] **Step 1: Add re-exports**

```python
"""aerocfd — aircraft CFD post-processing library."""
from aerocfd.models.aircraft import Aircraft
from aerocfd.models.alpha_case import AlphaCase, ConvergenceStatus
from aerocfd.models.dataset import AeroDataset
from aerocfd.models.operating_condition import OperatingCondition
from aerocfd.models.polar import Polar

__all__ = [
    "Aircraft",
    "AlphaCase",
    "ConvergenceStatus",
    "AeroDataset",
    "OperatingCondition",
    "Polar",
]
```

- [ ] **Step 2: Smoke test the re-exports**

Run:
```bash
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -c "from aerocfd import Aircraft, AlphaCase, AeroDataset, OperatingCondition, Polar, ConvergenceStatus; print('ok')"
```

Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add libs/aerocfd/src/aerocfd/__init__.py
git commit -m "feat(aerocfd): expose public API at top level"
```

---

## Task 10: aerocfd module page, descriptor & registry

**Owner:** Claude

**Files:**
- Create: `apps/aerisvault/src/aerisvault/modules/aerocfd/pages/polar.py` — the single page with `render()`
- Modify: `apps/aerisvault/src/aerisvault/modules/aerocfd/__init__.py` — the `ModuleDescriptor`
- Modify: `apps/aerisvault/src/aerisvault/portal/registry.py` — register the module

No tests — Streamlit pages are not unit-tested in v1 (per spec §9.5). Hand-tested in the browser at the end of slice 1 (Task 12). Note: the page is a `render()` function (no `st.set_page_config` — the shell owns that), per the portal module contract.

- [ ] **Step 1: Implement `modules/aerocfd/pages/polar.py`**

```python
"""aerocfd module — slice 1: single page, no database.

User enters Aircraft references, OC, and a small α-case table. Click "Plot"
to see CL–α, CD–α, L/D–α, CL–CD, Cm–α derived from raw body-frame loads.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from aerocfd import (
    AeroDataset, Aircraft, AlphaCase, ConvergenceStatus, OperatingCondition,
)
from aerocfd.viz.plot_utils import (
    cd_alpha_figure, cl_alpha_figure, cm_alpha_figure,
    drag_polar_figure, lift_to_drag_alpha_figure,
)


def render():
    st.title("aerocfd — Aircraft polar from raw Fluent loads")
    st.caption("Slice 1: in-memory only. Refreshing the page resets everything.")

    # ---- Aircraft section ----
    st.header("Aircraft")
    ac_col_a, ac_col_b, ac_col_c, ac_col_d = st.columns(4)
    ac_name = ac_col_a.text_input("Name", value="Reference")
    s_ref = ac_col_b.number_input("S_ref [m²]", min_value=0.0, value=10.0, step=0.1, format="%.4f")
    c_ref = ac_col_c.number_input("c_ref [m]", min_value=0.0, value=1.5, step=0.01, format="%.4f")
    b_ref = ac_col_d.number_input("b_ref [m]", min_value=0.0, value=8.0, step=0.1, format="%.4f")

    # ---- Operating condition section ----
    st.header("Operating condition")
    oc_col_a, oc_col_b, oc_col_c = st.columns(3)
    oc_name = oc_col_a.text_input("OC name", value="SL_50mps")
    velocity = oc_col_b.number_input("Velocity [m/s]", min_value=0.0, value=50.0, step=1.0)
    density = oc_col_c.number_input("Density [kg/m³]", min_value=0.0, value=1.225, step=0.001, format="%.4f")

    # ---- Alpha-cases table (body-frame totals; Fx is forward-positive, so a
    #      draggy body has negative Fx — the library turns that into positive drag) ----
    st.header("Alpha cases (body-frame totals)")
    default_rows = pd.DataFrame({
        "alpha_deg": [-5.0, 0.0, 5.0, 10.0, 15.0],
        "fx_n":      [-12.0, -10.0, -15.0, -30.0, -55.0],
        "fz_n":      [-300.0, 200.0, 700.0, 1200.0, 1600.0],
        "my_nm":     [-25.0, 0.0, 25.0, 50.0, 75.0],
        "convergence_status": [ConvergenceStatus.UNKNOWN.value] * 5,
    })
    status_options = [s.value for s in ConvergenceStatus]
    edited = st.data_editor(
        default_rows,
        num_rows="dynamic",
        column_config={
            "alpha_deg": st.column_config.NumberColumn("α [deg]", format="%.2f"),
            "fx_n": st.column_config.NumberColumn("Fx [N]", help="Body x, forward-positive; drag is -X so a draggy body has Fx<0", format="%.3f"),
            "fz_n": st.column_config.NumberColumn("Fz [N]", format="%.3f"),
            "my_nm": st.column_config.NumberColumn("My [N·m]", help="Raw Fluent My (sign-flipped in library)", format="%.3f"),
            "convergence_status": st.column_config.SelectboxColumn("Convergence", options=status_options),
        },
        use_container_width=True,
    )

    # ---- Plot button ----
    if st.button("Plot", type="primary"):
        aircraft = Aircraft(name=ac_name, s_ref_m2=s_ref, c_ref_m=c_ref, b_ref_m=b_ref)
        oc = OperatingCondition(name=oc_name, velocity_mps=velocity, density_kgpm3=density)
        cases = []
        for _, row in edited.iterrows():
            if pd.isna(row["alpha_deg"]):
                continue
            cases.append(AlphaCase(
                alpha_deg=float(row["alpha_deg"]),
                fx_n=float(row["fx_n"]),
                fz_n=float(row["fz_n"]),
                my_nm=float(row["my_nm"]),
                convergence_status=ConvergenceStatus(row["convergence_status"]),
            ))

        if len(cases) < 2:
            st.error("Need at least 2 α cases to plot a polar.")
        else:
            dataset = AeroDataset(aircraft=aircraft, operating_condition=oc, alpha_cases=cases)
            st.success(f"Built dataset with {len(cases)} cases. q∞ = {dataset.dynamic_pressure_pa:.2f} Pa.")

            cd_polar = dataset.cd()
            # Runtime echo of gold test #4: a negative CD signals a bad input
            # convention (wrong Fx sign). Non-blocking warning, per design §7.6.
            if np.any(cd_polar.values < 0):
                st.warning(
                    "Some CD values are negative. For a normal draggy body CD should be "
                    "positive — check that Fx follows the convention (forward-positive, "
                    "drag = -X). This usually means the input sign convention is off."
                )

            plot_col_a, plot_col_b = st.columns(2)
            plot_col_a.plotly_chart(cl_alpha_figure(dataset.cl()), use_container_width=True)
            plot_col_b.plotly_chart(cd_alpha_figure(cd_polar), use_container_width=True)

            plot_col_c, plot_col_d = st.columns(2)
            plot_col_c.plotly_chart(lift_to_drag_alpha_figure(dataset.lift_to_drag()), use_container_width=True)
            plot_col_d.plotly_chart(drag_polar_figure(dataset.cl(), cd_polar), use_container_width=True)

            st.plotly_chart(cm_alpha_figure(dataset.cm()), use_container_width=True)
```

- [ ] **Step 2: Implement the `ModuleDescriptor` in `modules/aerocfd/__init__.py`**

```python
"""aerocfd module — aircraft CFD polars (Fluent steady sweeps)."""
from aerisvault.portal.descriptor import ModuleDescriptor


def _pages():
    import streamlit as st
    from aerisvault.modules.aerocfd.pages import polar
    return [st.Page(polar.render, title="Polar", icon="✈️")]


MODULE = ModuleDescriptor(
    key="aerocfd",
    title="Aircraft CFD",
    icon="✈️",
    summary="Build aircraft aerodynamic polars from raw Fluent loads.",
    pages=_pages,
    order=20,
)
```

- [ ] **Step 3: Register the module in `portal/registry.py`**

Add the import and append to `MODULES`:

```python
from aerisvault.modules.fsi import MODULE as fsi
from aerisvault.modules.aerocfd import MODULE as aerocfd

MODULES = [fsi, aerocfd]
```

- [ ] **Step 4: Smoke import**

Run:
```bash
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -c "from aerisvault.modules.aerocfd import MODULE; from aerisvault.modules.aerocfd.pages.polar import render; print(MODULE.key, callable(render))"
```

Expected: `aerocfd True`.

- [ ] **Step 5: Commit**

```bash
git add apps/aerisvault/src/aerisvault/modules/aerocfd apps/aerisvault/src/aerisvault/portal/registry.py
git commit -m "feat(aerocfd): add slice-1 module page, descriptor, and registry entry"
```

---

## Task 11: Append `aerocfd` section to `CLAUDE.md`

**Owner:** Claude (drafts), Stepan (reviews before commit)

**Files:**
- Modify: `CLAUDE.md` (append a new top-level section after the existing architecture section, before any future sections)

- [ ] **Step 1: Read current `CLAUDE.md`**

Read `/home/stepan/projects/PhD/AerisVault/CLAUDE.md` to confirm the exact insertion point (end of "What does NOT exist yet" section).

- [ ] **Step 2: Append the new section**

Add this block at the end of `CLAUDE.md`:

```markdown

## aerocfd module (planned, in active development)

`libs/aerocfd/` is a new analytical library for aircraft CFD post-processing (Fluent steady polars). It is independent of `dynaprocessing` — neither imports the other. The aerocfd UI is a **module inside the `apps/aerisvault/` portal shell** (`apps/aerisvault/src/aerisvault/modules/aerocfd/`), registered via a `ModuleDescriptor` — not a standalone app. It delegates all computation to the library.

**Collaboration model.** This module is Stepan's learning project. Discuss before generating code; do not autonomously rewrite Stepan-owned modules. Per-module ownership split: Stepan writes the math and core classes (`Polar`, `AeroDataset`, `Aircraft`/`OperatingCondition`/`AlphaCase` dataclasses, `analysis/rotation.py`, `analysis/coefficients.py`, summation logic from slice 3); Claude writes scaffolding (ORM/mappers from slice 2, Streamlit pages, plot helpers, test fixtures and parametrize boilerplate). Per-module split is re-confirmed before each new module — fall back to discussion when uncertain. See memory: `feedback_aerocfd_learning_mode.md`.

**Axis convention (load-bearing, do not "fix" without asking).** Body frame: x = forward, z = up, right-handed → y points to the LEFT. α positive = nose up. Fluent reports the force ON the body in this fixed frame regardless of α — Stepan never redefines monitors per case. `Fx` is forward-positive, so a draggy body has `Fx < 0` (drag points −X); lift is +Z; nose-up moment is −Y. The library does the body→wind rotation `body_to_wind` (`D = −Fx·cosα + Fz·sinα`, `L = Fx·sinα + Fz·cosα`) and the My sign flip (`fluent_my_to_aero`, because Fluent's right-hand-rule My about +Y is nose-DOWN while aerospace Cm is nose-UP). Four "gold tests" in `tests/test_rotation.py` and `tests/test_dataset.py` enforce this — including `CD(α=0) > 0`, the one that catches an Fx-sign error. If they ever fail without an intentional convention change, there is a real bug. See memory: `project_aerocfd_axis_convention.md`, `project_aerocfd_fx_sign_open.md`.

**Group summation rule (slice 3+).** Rotate first, sum later. Each part's body-frame loads are rotated to wind frame, then summed. Mathematically equivalent to summing in body frame and rotating, but engineering questions live in wind frame. Coefficients are NEVER summed — only forces. Each part's CL contribution is `part_lift / (q∞ · S_ref)`.

**Library is ORM-free.** `libs/aerocfd/` never imports SQLAlchemy. From slice 2, ORM models live in `apps/aerisvault/src/aerisvault/modules/aerocfd/core/` with mapper functions translating to/from the library's frozen dataclasses. The library's plain types are the contract; the database is one of multiple possible storage layers.

**Single-user posture.** `aerocfd` is currently used only by Stepan, with future per-tool user separation in mind (hence its own SQLite file from slice 2). Mutable-state hazards (e.g. editing `S_ref` after polars are computed) get non-blocking UI warnings rather than snapshotting/freezing — proportional to single-user reality. Correctness risks (sign errors, unit mismatches) are still flagged forcefully. See memory: `project_single_user.md`.

**Versioning.** When bumping the unified monorepo version, update FIVE `pyproject.toml` files: root, `libs/dynaprocessing`, `libs/dynaprep`, `apps/aerisvault` (the renamed shell), and `libs/aerocfd`. There is no `apps/aerocfd-ui/pyproject.toml` — aerocfd's UI is a module inside the `aerisvault` shell.

**Common commands:**
```bash
# Run aerocfd library tests
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -v

# Start the portal shell, then open the "Aircraft CFD" card to reach the aerocfd module
cd apps/aerisvault
/home/stepan/projects/PhD/AerisVault/.venv/bin/streamlit run src/aerisvault/app.py

# Install the aerocfd library editable (the aerisvault shell is already installed)
/home/stepan/projects/PhD/AerisVault/.venv/bin/pip install -e libs/aerocfd
```

**Roadmap.** Slice 1 = totals → coefficients (no DB). Slice 2 = SQLite + multipage. Slice 3 = parts and groups (schema migration moment). Slice 4 = Cm dual path (manual + analytical). Slice 5 = comparison and CSV export. See `docs/superpowers/specs/2026-05-10-aerocfd-design.md`.
```

- [ ] **Step 3: Stepan reviews the appended section**

Pause here. Do not commit until Stepan reads the new section and confirms or requests changes.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add aerocfd module guidance to CLAUDE.md"
```

---

## Task 12: End-to-end manual smoke test

**Owner:** Stepan

**Files:** none (manual verification only)

- [ ] **Step 1: Start the portal shell and open the aerocfd module**

Run:
```bash
cd apps/aerisvault
/home/stepan/projects/PhD/AerisVault/.venv/bin/streamlit run src/aerisvault/app.py
```

Expected: the portal home lists tool cards. Click **"Aircraft CFD"** to enter the aerocfd module's Polar page.

- [ ] **Step 2: Verify default state renders**

On the aerocfd Polar page, confirm:
- Aircraft inputs show defaults (Reference, 10.0, 1.5, 8.0)
- Operating-condition inputs show defaults (SL_50mps, 50.0, 1.225)
- α-cases table has 5 rows with the default values
- Convergence-status column is a dropdown with all six enum values

- [ ] **Step 3: Click "Plot" and verify all five figures render**

- CL–α: roughly linear, slightly past zero at α=0
- CD–α: **positive everywhere**, low near α=0, rising at the extremes — confirms the Fx-sign rotation is correct (no negative-CD warning appears)
- L/D–α: peaks somewhere around α=5–10°
- CL–CD: the classic drag-polar shape
- Cm–α: **negative** for α > 0, **positive** for α < 0 — confirms the My sign-flip is alive end-to-end

- [ ] **Step 4: Edit the table and re-plot**

Change a few α values, add a row via the `+` button, click Plot again. Confirm the figures update.

- [ ] **Step 5: Run the full library test suite one more time**

Run:
```bash
cd libs/aerocfd
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -v
```

Expected: every test passes.

- [ ] **Step 6: Note in conversation that slice 1 is shippable**

No commit needed for this step; it's the human acceptance gate.

---

## Slice 1 Definition of Done

- All library tests pass.
- The four gold tests exist and pass: zero-α drag/lift (`drag=-Fx`, `lift=Fz`), pure-vertical-force at 10°, stable-airfoil Cm-negative-at-positive-α (sign-flip regression), and `CD(α=0) > 0`.
- The aerocfd module page (reached via the portal shell's "Aircraft CFD" card) renders five Plotly figures from the default-filled form, with no negative-CD warning.
- Editing the table and clicking Plot updates the figures.
- `CLAUDE.md` describes the aerocfd module (module-in-shell placement, axis/Fx convention, ownership split, ORM-free rule, versioning).
- All commits in place; working tree clean.
