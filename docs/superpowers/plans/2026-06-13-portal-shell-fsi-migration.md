# Portal Shell + FSI Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the AerisVault portal shell (one Streamlit app, modules as self-contained sections via an explicit registry + descriptor contract) and migrate the existing FSI app into it as module #1, proving the contract on real, tested code.

**Architecture:** A single Streamlit app at `apps/aerisvault/` renders a portal home from a registry of `ModuleDescriptor`s. Two-level navigation: the home lists tool cards; clicking one shows only that module's pages. Each module owns its DB/files under `data/<key>/` and delegates computation to a pure library in `libs/`. `libs/dynaprocessing` is not touched.

**Tech Stack:** Python 3, Streamlit (`st.navigation`/`st.Page`), SQLAlchemy 2.0, Plotly, pytest.

**Reference spec:** [`docs/superpowers/specs/2026-06-13-portal-architecture-design.md`](../specs/2026-06-13-portal-architecture-design.md)

**Environment:** all commands use the project venv: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python`.

---

## File Structure

**New (shell plumbing):**
- `apps/aerisvault/src/aerisvault/portal/descriptor.py` — `ModuleDescriptor` dataclass (the contract).
- `apps/aerisvault/src/aerisvault/portal/registry.py` — `MODULES` list (single source of truth).
- `apps/aerisvault/src/aerisvault/portal/home.py` — portal landing page (descriptor-driven cards).
- `apps/aerisvault/src/aerisvault/shared/paths.py` — `data_dir_for(key)`.
- `apps/aerisvault/src/aerisvault/shared/navigation.py` — `build_navigation(modules, active_module)`.
- `apps/aerisvault/src/aerisvault/app.py` — rewritten shell entry point.

**Relocated (FSI module, moved not rewritten):**
- `core/` → `modules/fsi/core/` (database.py, models.py, storage.py, config.py)
- `ui/` → `modules/fsi/ui/` (components.py)
- `pages/` → `modules/fsi/pages/` (database.py, single_analysis.py, comparison.py, settings.py — renamed, wrapped in `render()`)
- new `modules/fsi/core/bootstrap.py` — lazy session-state init under `fsi.*` keys.
- new `modules/fsi/__init__.py` — exposes `MODULE` descriptor.

**Tests (shell plumbing only — pages are hand-tested):**
- `apps/aerisvault/tests/test_descriptor.py`
- `apps/aerisvault/tests/test_registry.py`
- `apps/aerisvault/tests/test_paths.py`
- `apps/aerisvault/tests/test_navigation.py`

**Data layout target:** `data/fsi/aerisvault.db`, `data/fsi/config.json`, `data/fsi/raw/`, `data/fsi/processed/`.

---

## Task 1: Rename the app directory and fix packaging

**Files:**
- Move: `apps/aerisvault-ui/` → `apps/aerisvault/`
- Modify: `apps/aerisvault/pyproject.toml`

- [ ] **Step 1: Rename the directory with git**

```bash
cd /home/stepan/projects/PhD/AerisVault
git mv apps/aerisvault-ui apps/aerisvault
```

- [ ] **Step 2: Inspect the packaging file**

Run: `cat apps/aerisvault/pyproject.toml`
Look for any hard-coded `aerisvault-ui` name or path. Note the `[project] name` and any `[tool.setuptools]` package/path entries.

- [ ] **Step 3: Update the project name**

In `apps/aerisvault/pyproject.toml`, set the distribution name to match the new folder. Change the `[project]` name line:

```toml
[project]
name = "aerisvault"
```

Leave the import package (`src/aerisvault/`) unchanged — only the directory and distribution name change. Do not touch version (single unified version rule).

- [ ] **Step 4: Reinstall editable**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/pip install -e apps/aerisvault`
Expected: successful install, `Successfully installed aerisvault-<version>`.

- [ ] **Step 5: Verify the package imports**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -c "import aerisvault; print('ok')"`
Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add -A apps/aerisvault
git commit -m "refactor: rename apps/aerisvault-ui to apps/aerisvault (portal shell)"
```

---

## Task 2: ModuleDescriptor contract

**Files:**
- Create: `apps/aerisvault/src/aerisvault/portal/__init__.py` (empty)
- Create: `apps/aerisvault/src/aerisvault/portal/descriptor.py`
- Test: `apps/aerisvault/tests/test_descriptor.py`

- [ ] **Step 1: Write the failing test**

```python
# apps/aerisvault/tests/test_descriptor.py
"""Tests for the module contract (ModuleDescriptor)."""

import pytest
from aerisvault.portal.descriptor import ModuleDescriptor


def test_descriptor_is_frozen():
    """A descriptor must be immutable so a module's identity can't be mutated at runtime."""
    module = ModuleDescriptor(
        key="demo",
        title="Demo",
        icon="🧪",
        summary="A demo tool.",
        pages=lambda: [],
    )
    with pytest.raises(Exception):
        module.key = "changed"


def test_pages_is_callable_returning_list():
    """pages must be a zero-arg callable that returns a list (built lazily, not at import time)."""
    module = ModuleDescriptor(
        key="demo",
        title="Demo",
        icon="🧪",
        summary="A demo tool.",
        pages=lambda: ["page_a", "page_b"],
    )
    assert callable(module.pages)
    assert module.pages() == ["page_a", "page_b"]


def test_default_order_is_100():
    module = ModuleDescriptor(
        key="demo", title="Demo", icon="🧪", summary="x", pages=lambda: []
    )
    assert module.order == 100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/aerisvault && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_descriptor.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aerisvault.portal'`

- [ ] **Step 3: Create the package marker and the descriptor**

```python
# apps/aerisvault/src/aerisvault/portal/__init__.py
```

(empty file)

```python
# apps/aerisvault/src/aerisvault/portal/descriptor.py
"""The module contract: how a tool advertises itself to the portal shell."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModuleDescriptor:
    """How a tool advertises itself to the portal shell.

    A module is fully described by this object. The shell never reaches into a
    module's internals — it only reads this descriptor to build the landing page
    and the navigation menu.
    """

    key: str                       # stable id, e.g. "fsi"; also the data namespace (data/<key>/)
    title: str                     # shown on the card and menu, e.g. "Parachute FSI"
    icon: str                      # emoji or Streamlit material icon, e.g. "🪂"
    summary: str                   # one line for the portal card
    pages: Callable[[], list[Any]] # returns this module's st.Page list WHEN CALLED
    order: int = 100               # sort order on the portal home
```

`pages` is typed `Callable[[], list[Any]]` rather than `list[st.Page]` so this contract module does not import Streamlit (keeps it importable in plain pytest).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/aerisvault && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_descriptor.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add apps/aerisvault/src/aerisvault/portal apps/aerisvault/tests/test_descriptor.py
git commit -m "feat: add ModuleDescriptor contract"
```

---

## Task 3: Path resolution (`data_dir_for`)

**Files:**
- Create: `apps/aerisvault/src/aerisvault/shared/__init__.py` (empty)
- Create: `apps/aerisvault/src/aerisvault/shared/paths.py`
- Test: `apps/aerisvault/tests/test_paths.py`

- [ ] **Step 1: Write the failing test**

```python
# apps/aerisvault/tests/test_paths.py
"""Tests for per-module data directory resolution."""

from aerisvault.shared import paths


def test_data_dir_for_appends_key(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "DATA_ROOT", tmp_path)
    result = paths.data_dir_for("fsi")
    assert result == tmp_path / "fsi"


def test_data_dir_for_creates_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "DATA_ROOT", tmp_path)
    result = paths.data_dir_for("aerocfd")
    assert result.exists()
    assert result.is_dir()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/aerisvault && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_paths.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aerisvault.shared'`

- [ ] **Step 3: Create the package marker and the helper**

```python
# apps/aerisvault/src/aerisvault/shared/__init__.py
```

(empty file)

```python
# apps/aerisvault/src/aerisvault/shared/paths.py
"""Filesystem paths shared across the portal.

Every module's database and files live under data/<module_key>/. Modules never
hardcode paths — they resolve them through data_dir_for(key).
"""

from pathlib import Path

# Repo root is four parents up from this file:
# apps/aerisvault/src/aerisvault/shared/paths.py → AerisVault/
REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = REPO_ROOT / "data"


def data_dir_for(module_key: str) -> Path:
    """Return data/<module_key>/, creating it if needed."""
    path = DATA_ROOT / module_key
    path.mkdir(parents=True, exist_ok=True)
    return path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/aerisvault && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_paths.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add apps/aerisvault/src/aerisvault/shared apps/aerisvault/tests/test_paths.py
git commit -m "feat: add per-module data_dir_for path helper"
```

---

## Task 4: Navigation builder

**Files:**
- Create: `apps/aerisvault/src/aerisvault/shared/navigation.py`
- Test: `apps/aerisvault/tests/test_navigation.py`

The builder is pure logic over descriptors: it decides *which module's pages function* to call. It returns the selected module's `pages()` result, or `None` when no module is active (meaning: show the portal home). This keeps it unit-testable without Streamlit.

- [ ] **Step 1: Write the failing test**

```python
# apps/aerisvault/tests/test_navigation.py
"""Tests for the two-level navigation builder."""

from aerisvault.portal.descriptor import ModuleDescriptor
from aerisvault.shared.navigation import pages_for_active_module


def _module(key, marker):
    return ModuleDescriptor(
        key=key, title=key.upper(), icon="🧪", summary="x",
        pages=lambda: [f"{marker}-page"],
    )


def test_no_active_module_returns_none():
    """When no module is active, the shell shows the portal home (None = home)."""
    modules = [_module("fsi", "fsi"), _module("aerocfd", "cfd")]
    assert pages_for_active_module(modules, active_key=None) is None


def test_active_module_returns_only_its_pages():
    modules = [_module("fsi", "fsi"), _module("aerocfd", "cfd")]
    assert pages_for_active_module(modules, active_key="aerocfd") == ["cfd-page"]


def test_unknown_active_key_returns_none():
    """A stale/unknown active key falls back to the portal home rather than crashing."""
    modules = [_module("fsi", "fsi")]
    assert pages_for_active_module(modules, active_key="ghost") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/aerisvault && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_navigation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aerisvault.shared.navigation'`

- [ ] **Step 3: Write the implementation**

```python
# apps/aerisvault/src/aerisvault/shared/navigation.py
"""Two-level navigation: portal home, then one module at a time.

The pure decision (which module's pages to show) lives in
pages_for_active_module so it can be unit-tested without Streamlit. The
Streamlit wiring that turns that decision into st.navigation lives in app.py.
"""

from typing import Any, Optional

from aerisvault.portal.descriptor import ModuleDescriptor


def pages_for_active_module(
    modules: list[ModuleDescriptor],
    active_key: Optional[str],
) -> Optional[list[Any]]:
    """Return the active module's pages, or None to show the portal home.

    None is returned when no module is active OR when active_key does not match
    any registered module (a stale key falls back to the home page).
    """
    if active_key is None:
        return None
    for module in modules:
        if module.key == active_key:
            return module.pages()
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/aerisvault && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_navigation.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add apps/aerisvault/src/aerisvault/shared/navigation.py apps/aerisvault/tests/test_navigation.py
git commit -m "feat: add two-level navigation builder"
```

---

## Task 5: Relocate FSI `core/` into the module

**Files:**
- Move: `apps/aerisvault/src/aerisvault/core/` → `apps/aerisvault/src/aerisvault/modules/fsi/core/`
- Create: `apps/aerisvault/src/aerisvault/modules/__init__.py` (empty)
- Create: `apps/aerisvault/src/aerisvault/modules/fsi/__init__.py` (temporary empty; descriptor added in Task 9)

- [ ] **Step 1: Create the module package markers**

```bash
cd /home/stepan/projects/PhD/AerisVault/apps/aerisvault/src/aerisvault
mkdir -p modules/fsi
touch modules/__init__.py modules/fsi/__init__.py
```

- [ ] **Step 2: Move core into the module**

```bash
cd /home/stepan/projects/PhD/AerisVault/apps/aerisvault/src/aerisvault
git add -A   # stage the new package markers first
git mv core modules/fsi/core
```

- [ ] **Step 3: Verify internal core imports still resolve**

The files in `core/` import each other with relative imports (`from .models import ...`), so they need no change. Confirm:

Run: `cd /home/stepan/projects/PhD/AerisVault && grep -rn "from aerisvault.core" apps/aerisvault/src/aerisvault/modules/fsi/core/`
Expected: no matches (all intra-core imports are relative `from .`). If any absolute `aerisvault.core` import appears, change it to `aerisvault.modules.fsi.core`.

- [ ] **Step 4: Verify the moved package imports**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -c "from aerisvault.modules.fsi.core.models import Simulation; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
cd /home/stepan/projects/PhD/AerisVault
git add -A apps/aerisvault/src/aerisvault/modules
git commit -m "refactor: move FSI core into modules/fsi/core"
```

---

## Task 6: Point FSI storage and config at `data/fsi/`

**Files:**
- Modify: `apps/aerisvault/src/aerisvault/modules/fsi/core/config.py`
- Create: `apps/aerisvault/src/aerisvault/modules/fsi/core/bootstrap.py`
- Move (data, if present): existing `aerisvault.db`, `config.json`, `data/raw`, `data/processed` into `data/fsi/`

- [ ] **Step 1: Migrate existing data into data/fsi/ (one-time)**

```bash
cd /home/stepan/projects/PhD/AerisVault
mkdir -p data/fsi
# Move existing DB and config if they exist at repo root:
[ -f aerisvault.db ] && git mv aerisvault.db data/fsi/aerisvault.db || echo "no root db"
[ -f config.json ] && git mv config.json data/fsi/config.json || echo "no root config"
# Move existing raw/processed sim folders under data/fsi/:
[ -d data/raw ] && git mv data/raw data/fsi/raw || echo "no raw dir"
[ -d data/processed ] && git mv data/processed data/fsi/processed || echo "no processed dir"
```

Note: stored `File.storage_path` values in the DB are absolute/relative paths to the old `data/raw|processed` location. Because this is single-user dev data, the accepted approach is to re-upload files if paths break, OR (if you want to preserve them) run a one-off SQL update. For this migration, document that previously-uploaded file paths may need re-attaching; the DB rows and metadata are preserved.

- [ ] **Step 2: Update config to resolve its path under data/fsi/**

Replace the bottom of `apps/aerisvault/src/aerisvault/modules/fsi/core/config.py` (the `get_settings` function and module-global) with:

```python
# Global settings instance
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Load FSI settings from data/fsi/config.json (created on first save)."""
    global _settings
    if _settings is None:
        from aerisvault.shared.paths import data_dir_for
        config_path = str(data_dir_for("fsi") / "config.json")
        _settings = AppSettings.load(config_path)
    return _settings
```

Leave the `AppSettings`/`FilterSettings`/`PlotSettings` dataclasses unchanged.

- [ ] **Step 3: Create the FSI bootstrap helper (namespaced session state)**

```python
# apps/aerisvault/src/aerisvault/modules/fsi/core/bootstrap.py
"""Lazy initialization of the FSI module's session-state objects.

All keys are namespaced with the module key ("fsi.*") so this module cannot
collide with other modules' session state. Called at the top of every FSI page.
"""

import streamlit as st

from aerisvault.modules.fsi.core.config import get_settings
from aerisvault.modules.fsi.core.database import SimulationDatabase
from aerisvault.modules.fsi.core.storage import StorageManager
from aerisvault.shared.paths import data_dir_for


def ensure_initialized() -> None:
    """Create the FSI DB, storage, and settings once per session, namespaced."""
    if "fsi.db" not in st.session_state:
        fsi_dir = data_dir_for("fsi")
        settings = get_settings()
        st.session_state["fsi.db"] = SimulationDatabase(
            f"sqlite:///{fsi_dir / settings.db_name}"
        )
        st.session_state["fsi.storage"] = StorageManager(str(fsi_dir))
        st.session_state["fsi.settings"] = settings
```

`StorageManager(str(fsi_dir))` makes `data/fsi/raw` and `data/fsi/processed` its base — matching the migrated layout. No change to `storage.py` is needed.

- [ ] **Step 4: Verify imports**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -c "from aerisvault.modules.fsi.core.bootstrap import ensure_initialized; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
cd /home/stepan/projects/PhD/AerisVault
git add -A
git commit -m "refactor: FSI storage/config under data/fsi, add namespaced bootstrap"
```

---

## Task 7: Relocate FSI `ui/` and wrap pages in `render()`

**Files:**
- Move: `apps/aerisvault/src/aerisvault/ui/` → `apps/aerisvault/src/aerisvault/modules/fsi/ui/`
- Move + transform: `pages/01_database.py` → `modules/fsi/pages/database.py` (and the other three)

- [ ] **Step 1: Move the ui package**

```bash
cd /home/stepan/projects/PhD/AerisVault/apps/aerisvault/src/aerisvault
git mv ui modules/fsi/ui
```

- [ ] **Step 2: Fix component imports inside pages later; move the pages now**

```bash
cd /home/stepan/projects/PhD/AerisVault/apps/aerisvault/src/aerisvault
mkdir -p modules/fsi/pages
touch modules/fsi/pages/__init__.py
git mv pages/01_database.py        modules/fsi/pages/database.py
git mv pages/02_single_analysis.py modules/fsi/pages/single_analysis.py
git mv pages/03_comparison.py      modules/fsi/pages/comparison.py
git mv pages/04_settings.py        modules/fsi/pages/settings.py
# remove the now-empty Streamlit-convention pages package
git rm pages/__init__.py
```

- [ ] **Step 3: Apply the uniform page transform to all four page files**

Each page currently has this shape:

```python
"""docstring"""
import streamlit as st
... other imports ...
st.set_page_config(page_title="...", page_icon="...", layout="wide")
db = st.session_state.db
storage = st.session_state.storage   # (settings.py uses st.session_state.settings)
<top-level body>
```

Transform each file with these four exact edits:

1. **Rewrite the import block** — replace any `from aerisvault.core.<x>` with `from aerisvault.modules.fsi.core.<x>`, and `from aerisvault.ui.components` with `from aerisvault.modules.fsi.ui.components`. Add `from aerisvault.modules.fsi.core.bootstrap import ensure_initialized`.
2. **Delete the `st.set_page_config(...)` line.** The shell sets page config once; a module page must not call it.
3. **Wrap the body in a function.** Insert `def render():` after the imports, then indent everything from the old `db = st.session_state...` line to the end of the file by four spaces. As the first line inside `render()`, add `ensure_initialized()`.
4. **Re-source the managers from namespaced keys** — the lines that were `db = st.session_state.db` / `storage = st.session_state.storage` / `settings = st.session_state.settings` become `db = st.session_state["fsi.db"]` / `storage = st.session_state["fsi.storage"]` / `settings = st.session_state["fsi.settings"]`.

Worked example — `modules/fsi/pages/database.py` header after transform (body unchanged below the shown lines, just indented):

```python
"""
AerisVault FSI - Database Page
Simulation registry: browse, add, edit, delete simulations and manage tags.
"""

import streamlit as st
import pandas as pd
from aerisvault.modules.fsi.core.models import FileType
from aerisvault.modules.fsi.core.bootstrap import ensure_initialized


def render():
    ensure_initialized()
    db = st.session_state["fsi.db"]
    storage = st.session_state["fsi.storage"]

    st.title("🗄️ Simulation Database")
    # ... rest of the original body, indented four spaces ...
```

`settings.py` has no `db`/`storage`; it only uses `settings = st.session_state.settings` → `settings = st.session_state["fsi.settings"]`, and still calls `ensure_initialized()` first so the settings object exists.

- [ ] **Step 4: Verify each page module imports and exposes render**

Run:
```bash
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -c "
from aerisvault.modules.fsi.pages import database, single_analysis, comparison, settings
for m in (database, single_analysis, comparison, settings):
    assert callable(m.render), m.__name__
print('ok')
"
```
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
cd /home/stepan/projects/PhD/AerisVault
git add -A apps/aerisvault/src/aerisvault/modules/fsi
git commit -m "refactor: wrap FSI pages in render() and relocate into modules/fsi"
```

---

## Task 8: FSI module descriptor + registry

**Files:**
- Modify: `apps/aerisvault/src/aerisvault/modules/fsi/__init__.py`
- Create: `apps/aerisvault/src/aerisvault/portal/registry.py`
- Test: `apps/aerisvault/tests/test_registry.py`

- [ ] **Step 1: Write the failing registry contract test**

```python
# apps/aerisvault/tests/test_registry.py
"""Contract tests: every registered module must satisfy the descriptor invariants."""

from aerisvault.portal.registry import MODULES
from aerisvault.portal.descriptor import ModuleDescriptor


def test_registry_is_non_empty():
    assert len(MODULES) >= 1


def test_all_entries_are_descriptors():
    assert all(isinstance(m, ModuleDescriptor) for m in MODULES)


def test_keys_are_unique_and_lowercase():
    keys = [m.key for m in MODULES]
    assert len(keys) == len(set(keys)), "duplicate module keys"
    assert all(k == k.lower() and k for k in keys), "keys must be non-empty lowercase"


def test_titles_non_empty_and_pages_callable():
    for m in MODULES:
        assert m.title.strip(), f"{m.key} has empty title"
        assert callable(m.pages), f"{m.key} pages is not callable"


def test_fsi_module_registered():
    assert any(m.key == "fsi" for m in MODULES)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/aerisvault && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aerisvault.portal.registry'`

- [ ] **Step 3: Define the FSI descriptor**

```python
# apps/aerisvault/src/aerisvault/modules/fsi/__init__.py
"""FSI module: post-processing of LS-DYNA parachute force histories."""

from aerisvault.portal.descriptor import ModuleDescriptor


def _pages():
    import streamlit as st
    from aerisvault.modules.fsi.pages import (
        database,
        single_analysis,
        comparison,
        settings,
    )
    return [
        st.Page(database.render,        title="Database",        icon="🗄️"),
        st.Page(single_analysis.render, title="Single Analysis", icon="📈"),
        st.Page(comparison.render,      title="Comparison",      icon="⚖️"),
        st.Page(settings.render,        title="Settings",        icon="⚙️"),
    ]


MODULE = ModuleDescriptor(
    key="fsi",
    title="Parachute FSI",
    icon="🪂",
    summary="Post-process LS-DYNA parachute force histories.",
    pages=_pages,
    order=10,
)
```

- [ ] **Step 4: Create the registry**

```python
# apps/aerisvault/src/aerisvault/portal/registry.py
"""The single source of truth for which tools the platform exposes.

Adding a tool: create its module package exposing a MODULE descriptor, then
append it here.
"""

from aerisvault.modules.fsi import MODULE as fsi
# from aerisvault.modules.aerocfd import MODULE as aerocfd   # added when aerocfd lands

MODULES = [fsi]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd apps/aerisvault && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_registry.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
cd /home/stepan/projects/PhD/AerisVault
git add apps/aerisvault/src/aerisvault/modules/fsi/__init__.py apps/aerisvault/src/aerisvault/portal/registry.py apps/aerisvault/tests/test_registry.py
git commit -m "feat: register FSI module in the portal registry"
```

---

## Task 9: Portal home page

**Files:**
- Create: `apps/aerisvault/src/aerisvault/portal/home.py`

This page renders one card per module from the registry and sets `active_module` when a card's button is clicked. No unit test (Streamlit rendering; hand-tested in Task 11).

- [ ] **Step 1: Write the home page**

```python
# apps/aerisvault/src/aerisvault/portal/home.py
"""Portal landing page: one card per registered tool."""

import streamlit as st

from aerisvault.portal.registry import MODULES


def render():
    st.title("🚀 AerisVault")
    st.caption("A home for your engineering simulation tools.")
    st.divider()

    modules = sorted(MODULES, key=lambda m: m.order)
    columns = st.columns(3)
    for index, module in enumerate(modules):
        with columns[index % 3]:
            st.subheader(f"{module.icon} {module.title}")
            st.write(module.summary)
            if st.button(f"Open {module.title}", key=f"open_{module.key}", type="primary"):
                st.session_state["active_module"] = module.key
                st.rerun()
```

- [ ] **Step 2: Verify import**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -c "from aerisvault.portal.home import render; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add apps/aerisvault/src/aerisvault/portal/home.py
git commit -m "feat: add portal home page (descriptor-driven cards)"
```

---

## Task 10: Shell entry point (`app.py`)

**Files:**
- Modify (full rewrite): `apps/aerisvault/src/aerisvault/app.py`

This wires the two-level navigation: portal home when no module is active; otherwise the active module's pages plus a "← All tools" control. No unit test (Streamlit wiring; hand-tested in Task 11).

- [ ] **Step 1: Rewrite app.py**

```python
# apps/aerisvault/src/aerisvault/app.py
"""AerisVault portal shell.

One Streamlit app hosting many tools as self-contained modules. The portal home
lists the tools; selecting one shows only that module's pages (two-level
navigation). Run with:

    streamlit run apps/aerisvault/src/aerisvault/app.py
"""

import streamlit as st

from aerisvault.portal.home import render as render_home
from aerisvault.portal.registry import MODULES
from aerisvault.shared.navigation import pages_for_active_module

st.set_page_config(
    page_title="AerisVault",
    page_icon="🪂",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _go_home():
    st.session_state["active_module"] = None


active_key = st.session_state.get("active_module")
module_pages = pages_for_active_module(MODULES, active_key)

if module_pages is None:
    # No module selected (or stale key) → portal home.
    home_page = st.Page(render_home, title="All tools", icon="🏠")
    st.navigation([home_page]).run()
else:
    # Inside a module → only its pages, plus a way back to the portal.
    st.sidebar.button("← All tools", on_click=_go_home, use_container_width=True)
    active_module = next(m for m in MODULES if m.key == active_key)
    st.sidebar.title(f"{active_module.icon} {active_module.title}")
    st.navigation(module_pages).run()
```

- [ ] **Step 2: Verify import (no Streamlit runtime needed for import)**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -c "import aerisvault.app; print('ok')"`
Expected: `ok` (Streamlit may print a bare-mode warning; that is fine).

- [ ] **Step 3: Run the full shell test suite**

Run: `cd apps/aerisvault && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -v`
Expected: all tests pass (descriptor, paths, navigation, registry).

- [ ] **Step 4: Confirm the FSI library is still green (nothing in libs moved)**

Run: `cd libs/dynaprocessing && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -q`
Expected: all existing tests pass.

- [ ] **Step 5: Commit**

```bash
cd /home/stepan/projects/PhD/AerisVault
git add apps/aerisvault/src/aerisvault/app.py
git commit -m "feat: portal shell entry with two-level navigation"
```

---

## Task 11: Browser hand-test

**Files:** none (manual verification).

- [ ] **Step 1: Launch the shell**

Run: `cd /home/stepan/projects/PhD/AerisVault/apps/aerisvault && /home/stepan/projects/PhD/AerisVault/.venv/bin/streamlit run src/aerisvault/app.py`

- [ ] **Step 2: Verify the portal home**

Expected: a "🚀 AerisVault" page with one card: "🪂 Parachute FSI" and an "Open Parachute FSI" button.

- [ ] **Step 3: Enter the FSI module**

Click "Open Parachute FSI". Expected: sidebar shows "← All tools", the "🪂 Parachute FSI" header, and the four pages (Database, Single Analysis, Comparison, Settings). The Database page lists existing simulations from `data/fsi/aerisvault.db`.

- [ ] **Step 4: Exercise each page**

Click through Database (registry loads), Single Analysis, Comparison, Settings. Expected: no `KeyError: 'db'`, no `set_page_config` errors, plots render.

- [ ] **Step 5: Return to the portal**

Click "← All tools". Expected: back to the portal home; `active_module` cleared.

- [ ] **Step 6: Stop the server** (Ctrl-C).

---

## Task 12: Update docs and version-bump checklist

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/architecture.md`

- [ ] **Step 1: Update CLAUDE.md architecture section**

In `CLAUDE.md`, replace the directory-layout block and add a "Portal architecture" note describing: one shell app at `apps/aerisvault/`, modules under `src/aerisvault/modules/<key>/`, the `ModuleDescriptor` + `registry.py` contract, two-level navigation, per-module DB under `data/<key>/`, and session-state key namespacing (`<key>.*`). Update the version-bump checklist path `apps/aerisvault-ui/pyproject.toml` → `apps/aerisvault/pyproject.toml`. Update the "Start the Streamlit app" command to `cd apps/aerisvault && .venv/bin/streamlit run src/aerisvault/app.py`.

- [ ] **Step 2: Update docs/architecture.md**

Update §3 (System Components), §4 (Directory Structure), and §5 (Data Flow) to describe the portal shell, modules, and `data/<key>/` layout. Mark `aerisvault-ui` references as the renamed `aerisvault` shell.

- [ ] **Step 3: Commit**

```bash
cd /home/stepan/projects/PhD/AerisVault
git add CLAUDE.md docs/architecture.md
git commit -m "docs: describe portal architecture and module contract"
```

---

## Self-Review notes

- **Spec coverage:** §3 layout → Tasks 1,5,7; §4 contract → Tasks 2,8; §5 navigation → Tasks 4,9,10; §6 shared/module split + namespacing → Tasks 3,6,7; §8 first-build (rename, relocate, render(), data move) → Tasks 1,5,6,7; §10 testing → Tasks 2,3,4,8 + Task 11 hand-test; §12 versioning + CLAUDE.md → Task 12. `libs/dynaprocessing` untouched, verified in Task 10 Step 4.
- **aerocfd reconciliation (§9):** intentionally not in this plan — it's a later cycle; registry leaves a commented placeholder line (Task 8).
- **Risk note:** stored `File.storage_path` values may point at the pre-move `data/raw|processed` location (flagged in Task 6 Step 1). Accepted for single-user dev data; re-attach files if a path breaks.
```
