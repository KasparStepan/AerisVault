# AerisVault Portal Architecture — Design

**Status:** Draft (awaiting Stepan's review)
**Date:** 2026-06-13
**Authors:** Stepan + Claude (brainstorming session)
**Related:** [`docs/architecture.md`](../../architecture.md), [`docs/superpowers/specs/2026-05-10-aerocfd-design.md`](2026-05-10-aerocfd-design.md)

---

## 1. Overview

This document designs the **portal architecture** for AerisVault: a single web platform whose landing page lists a growing set of engineering tools (currently parachute FSI post-processing; next, aircraft CFD; later, things like a weather app). Clicking a tool takes the user into that tool's own self-contained world.

The core idea: **one Streamlit shell, many modules, many libraries, one repository.** Each tool is a *module* — a group of pages plus its own database — that delegates all computation to a pure, independently installable *library*. Adding a new tool in the future is a fixed, three-step recipe with no changes to the shell or to other modules.

This spec covers only the **platform/portal architecture**. The migration of the existing FSI app and the build of the aerocfd module are separate work, scoped in §6.

### 1.1 Motivating vision (Stepan's words)

> "One website. On the title page there will be a list of all my different databases — one dynaprocessing, one aerocfd. Each will be a separate application with different features. Multiple libraries, but one big project, so in future I can add a new application or module — for example a weather app, which leads to a completely separate module."

### 1.2 Guiding constraints

- **Maintained by a mechanical engineer, in Python, for years.** Readable and explicit over clever; no framework magic that hides where things come from.
- **Libraries stay pure and independently usable.** The reusable, publishable value lives in `libs/`; the UI is thin, replaceable glue.
- **Single repository (monorepo).** Package boundaries are clean; repository boundaries stay simple. Individual libraries can still be published to PyPI from the monorepo.
- **Easy extension.** Adding a module must be obvious and low-ceremony.

## 2. Decisions settled in brainstorming

| Topic | Choice | Reasoning (brief) |
|---|---|---|
| Platform shape | Portal of tools | Title page lists tools; each tool is its own world. Matches Stepan's mental model. |
| Runtime model | One Streamlit app, modules as sections | Native to Streamlit (`st.navigation`); one process, one URL, one command; trivial to add a module. |
| Module contract | Explicit registry + small descriptor | A single `registry.py` lists every module; readable at a glance, no auto-discovery magic. |
| Navigation feel | Two-level: portal home, then one module at a time | Sidebar shows only the active module's pages; matches "separate world" feel; scales as modules grow. |
| Repository | Monorepo | One developer; shared version and conventions; PyPI publishing still possible per-package. |
| DB ownership | One DB per module under `data/<key>/` | No central schema; modules are sealed and independently deletable. |
| UI framework | Streamlit (stay) | Best fit for a solo Python-maintainer building data/engineering tools with small data. Engines are framework-agnostic, so the choice is reversible at low cost. |
| First implementation | Shell + FSI migration together | The module contract can only be validated against a real module; FSI is working, tested code — the safest proving ground. |

## 3. Architecture

### 3.1 Directory layout

```
AerisVault/
├── libs/                          ← computation only; pure, tested, publishable
│   ├── dynaprocessing/            ← FSI engine (UNTOUCHED by this work)
│   └── aerocfd/                   ← CFD engine (built later, its own spec)
│
├── apps/
│   ├── aerisvault/                ← THE shell app (renamed from aerisvault-ui)
│   │   ├── pyproject.toml
│   │   └── src/aerisvault/
│   │       ├── app.py             ← entry point: builds navigation from registry, runs
│   │       ├── portal/
│   │       │   ├── descriptor.py  ← ModuleDescriptor dataclass (the contract)
│   │       │   ├── registry.py    ← MODULES = [...]  (single source of truth)
│   │       │   └── home.py        ← landing page: one card per module
│   │       ├── shared/            ← cross-module plumbing (chrome, nav builder, paths, config)
│   │       │   ├── paths.py       ← data_dir_for(key)
│   │       │   ├── navigation.py  ← MODULES + active_module → st.navigation
│   │       │   ├── config.py      ← tiny global config (e.g. theme)
│   │       │   └── components.py  ← only genuinely generic widgets
│   │       └── modules/
│   │           ├── fsi/           ← FSI module = current aerisvault-ui, relocated
│   │           │   ├── __init__.py   ← exposes MODULE (ModuleDescriptor)
│   │           │   ├── pages/        ← database, single_analysis, comparison, settings
│   │           │   ├── core/         ← database.py, models.py, storage.py → owns data/fsi/aerisvault.db
│   │           │   └── ui/           ← FSI-specific components
│   │           └── aerocfd/       ← CFD module (built later)
│   │               ├── __init__.py
│   │               ├── pages/
│   │               ├── core/         ← owns data/aerocfd/aerocfd.db
│   │               └── ui/
│   │
│   └── aerisvault-old/            ← legacy, reference only, untouched
│
└── data/                          ← each module's DB + files under its own subfolder
    ├── fsi/                       ← aerisvault.db, config.json, raw/, processed/
    └── aerocfd/                   ← aerocfd.db
```

### 3.2 The three structural rules

1. **Libraries never move and never import upward.** `dynaprocessing` and `aerocfd` stay pure, tested, independently installable, publishable. The shell is the only layer that knows modules exist.
2. **A module is self-contained.** Its pages, its ORM/DB (`core/`), and its widgets (`ui/`) live in one folder and delegate computation to its library. One module can be read, rebuilt, or deleted without touching another.
3. **Each module owns its own database** under `data/<key>/`. The shell holds no central schema — only the registry of which modules exist.

### 3.3 Framework independence

Only `app.py`, `portal/home.py`, and `shared/navigation.py` are Streamlit-specific. The module contract (`descriptor.py`, `registry.py`), the `data/<key>/` convention, per-module databases, and the libraries are plain Python that would survive a future framework swap. Choosing Streamlit now is therefore low-risk and reversible.

## 4. The module contract

A module advertises itself to the shell through one small, frozen dataclass. The shell sees only this descriptor; it never reaches into a module's internals.

### 4.1 `portal/descriptor.py`

```python
from dataclasses import dataclass
from collections.abc import Callable
import streamlit as st


@dataclass(frozen=True)
class ModuleDescriptor:
    """How a tool advertises itself to the portal shell.

    A module is fully described by this object. The shell never reaches
    into a module's internals — it only reads this descriptor to build
    the landing page and the navigation menu.
    """
    key: str                            # stable id, e.g. "fsi", "aerocfd"; also the data namespace
    title: str                          # shown on card and menu, e.g. "Parachute FSI"
    icon: str                           # emoji or Streamlit material icon, e.g. "🪂"
    summary: str                        # one line for the portal card
    pages: Callable[[], list[st.Page]]  # returns this module's nav pages WHEN CALLED
    order: int = 100                    # sort order on the portal home
```

Two design points:

- **`pages` is a callable, not a list.** It constructs the `st.Page` objects (and triggers their imports) only when the shell builds navigation — not at registry-import time. This keeps one module's import error from taking down the whole portal and keeps startup cheap.
- **`key` doubles as the data namespace.** A module's DB and files live under `data/<key>/`, so `key` is the one string tying identity to storage. Stable, lowercase, never reused.

### 4.2 Each module exposes its descriptor

```python
# modules/fsi/__init__.py
from aerisvault.portal.descriptor import ModuleDescriptor


def _pages():
    import streamlit as st
    from aerisvault.modules.fsi.pages import database, single_analysis, comparison, settings
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

The contract governs only *how* a module plugs in — not *what* pages it may contain. A module is free to add any domain-specific pages it likes (e.g. aerocfd's planned multi-plane comparison, semi-empirical analytical model, and curve-fitting pages). The shell neither knows nor cares.

### 4.3 `portal/registry.py` — the single source of truth

```python
from aerisvault.modules.fsi import MODULE as fsi
# from aerisvault.modules.aerocfd import MODULE as aerocfd   # added when aerocfd lands

MODULES = [fsi]
```

The entire platform is legible from this one file. Adding a tool = create its package, expose a `MODULE`, append one line here.

## 5. Portal home & navigation behavior

### 5.1 Landing page

`portal/home.py` reads `MODULES` (sorted by `order`) and renders one card per tool: icon, title, one-line summary, and a button to enter. No module-specific knowledge — purely descriptor-driven.

### 5.2 Two-level navigation (the chosen feel)

- The portal home is the entry point. Clicking a module's card sets `st.session_state["active_module"]` to that module's `key`.
- `shared/navigation.py` then rebuilds `st.navigation` with **only the active module's pages**, plus a "← All tools" control that clears `active_module` and returns to the portal.
- The user is inside one tool at a time; the sidebar stays focused no matter how many modules exist.

The navigation builder is the only non-trivial shell logic (~15 lines), written once and untouched as modules are added.

## 6. What's shared vs module-owned

The dividing line is strict: **`shared/` holds platform plumbing only — never domain logic.**

### 6.1 `shared/` contains

- **Portal chrome** — page config, header/footer, the "← All tools" control, theme.
- **Navigation builder** — `MODULES` + `active_module` → the correct `st.navigation` call.
- **Path resolution** — one helper so modules never hardcode paths:
  ```python
  # shared/paths.py
  def data_dir_for(module_key: str) -> Path:
      """Every module's DB and files live under data/<key>/."""
      path = DATA_ROOT / module_key
      path.mkdir(parents=True, exist_ok=True)
      return path
  ```
- **Common UI helpers** — only genuinely generic widgets (e.g. a confirm-delete dialog). Domain widgets stay in the module's own `ui/`.

### 6.2 `shared/` must NOT contain

Any ORM model, DB session, solver/analysis call, or anything specific to FSI or CFD. If a thing knows what a parachute or an aircraft is, it lives in a module.

### 6.3 Each module owns

- Its **database** — `core/` builds its own engine against `data/<key>/<key>.db` (FSI keeps the name `aerisvault.db`), resolved via `data_dir_for(key)`. No central schema, no shared `Base`.
- Its **config** — module-specific settings. FSI's filter/plot defaults (currently the root `config.json`) move to `data/fsi/config.json`. The shell keeps only a tiny global config (e.g. theme). A module never reads another module's config.

### 6.4 Session-state namespacing

`st.session_state` is one flat dict shared across the whole process, so modules must not collide on keys. **Convention: every module prefixes its keys with its `key`** — `fsi.current_sim_id`, `aerocfd.current_aircraft_id`. The shell owns exactly one reserved key: `active_module`. Enforced by code review, not by the framework, but it prevents the worst class of multi-module bug (one tool clobbering another's state).

The net effect: a module is a sealed unit. Deleting `modules/aerocfd/` and `data/aerocfd/` leaves the FSI tool unaffected.

## 7. Scope

### 7.1 In scope (this document designs)

- The shell app, portal home (Pattern B two-level navigation), the module contract (`ModuleDescriptor` + `registry.py`), `shared/` plumbing, the `data/<key>/` + DB-per-module convention, session-state namespacing, and the `apps/aerisvault-ui` → `apps/aerisvault` rename.
- The **first implementation** also migrates the existing FSI app into the shell as module #1 (see §8), to prove the contract on real code.

### 7.2 Out of scope (each gets its own spec → plan → build cycle later)

- **aerocfd build** — the existing aerocfd spec + slices, executed under the module placement (see §9).
- **Publishing libraries to PyPI** — hygiene on top of the existing clean package boundaries; not required for the platform to work.
- **Auth / hosting / public-facing concerns** — revisited only if a genuine high-traffic public-product goal appears, at which point the framework-agnostic engines allow swapping the shell.
- **Future modules** — weather, `simtracker`, etc.

## 8. First implementation: shell + FSI migration

The first plan builds the shell and folds the existing FSI app in as module #1. This involves:

- **Rename** `apps/aerisvault-ui` → `apps/aerisvault`; the package stays `aerisvault` but becomes the platform shell.
- **Relocate** the current FSI pages, `core/` (database, models, storage), and `ui/` into `modules/fsi/`.
- **Wrap each page** in an explicit `render()` function so it can be referenced by `st.Page` (moving away from Streamlit's filename-based `pages/NN_*.py` auto-discovery toward the modern `st.navigation` API). Mechanical, low-risk; page bodies move into a function.
- **Move FSI data** under `data/fsi/` — `aerisvault.db`, `config.json`, and the existing `raw/`/`processed/` storage paths; update `core/storage.py` and `core/config.py` to resolve via `data_dir_for("fsi")`.
- **Build the shell** — `app.py`, `portal/` (descriptor, registry, home), `shared/` (paths, navigation, config, components).

**`libs/dynaprocessing` is not touched.** All FSI computation continues to live there; only the app-side glue moves. The 100+ library tests keep passing because nothing they depend on moves.

`CLAUDE.md` is updated in this cycle to describe the portal/module structure and the version-bump path change.

## 9. Reconciliation with the aerocfd spec

The [aerocfd v1 design](2026-05-10-aerocfd-design.md) survives almost intact. Its math, library structure (`libs/aerocfd/`), database schema, five-slice progression, and learning split are unaffected. One amendment is needed when the aerocfd cycle starts:

- **Before:** standalone app at `apps/aerocfd-ui/` with its own `core/` and `pages/`.
- **After:** a module at `apps/aerisvault/src/aerisvault/modules/aerocfd/`; its `core/` and `pages/` live in the module folder, it exposes a `ModuleDescriptor`, and it is registered in `registry.py`. The library `libs/aerocfd/` does not change.

Happy alignments: the aerocfd spec already targets `data/aerocfd/aerocfd.db` (exactly the `data/<key>/` convention), and its "separate DB" decision still holds — only the "separate process" framing changes to "module in the shell." Per-tool user separation, if ever needed, becomes a portal/auth concern, not a reason to run separate processes.

This amendment is applied when the aerocfd cycle begins, not in this spec.

## 10. Testing

- **Libraries** keep their full test suites, unchanged. Engineering correctness lives here.
- **Shell plumbing** gets a small, pure-Python suite (no Streamlit needed):
  - *Registry contract test* — every descriptor has a unique `key`, non-empty `title`, and a callable `pages`.
  - *Navigation builder test* — given `MODULES` + an `active_module`, the builder returns the right page set (portal home when none selected; one module's pages when selected).
  - *Path resolution test* — `data_dir_for(key)` maps to `data/<key>/` and creates it.
- **Streamlit pages** are hand-tested in the browser, not unit-tested — same convention as the current app and the aerocfd spec (§9.5). Their only failure modes are glue, found in seconds by clicking through.

## 11. Adding a new module (the extensibility recipe)

1. *(If it needs new computation)* create `libs/<engine>/` — a pure library, same pattern as `dynaprocessing`. A tool that only calls an external API may skip this.
2. Create `modules/<key>/`: `__init__.py` exposing a `MODULE` descriptor, `pages/` (with `render()` functions), `core/` if it has its own DB, `ui/` for its widgets.
3. Append one line to `registry.py`.
4. Its data lands in `data/<key>/` automatically via `data_dir_for(key)`.

No shell code changes; no other module touched.

## 12. Versioning

The monorepo's single unified version rule (per `CLAUDE.md`) is unchanged. The rename changes one path in the version-bump checklist: `apps/aerisvault-ui/pyproject.toml` → `apps/aerisvault/pyproject.toml`.

## 13. What's next

1. Brainstorming transitions to `superpowers:writing-plans` to produce the implementation plan for §8 (shell + FSI migration).
2. After this platform work, take a closer look at `dynaprocessing` (Stepan's request) — review and refine the FSI library before/alongside its relocation.
3. The aerocfd cycle (§9) follows as its own spec amendment → plan → build.

---

*End of design.*
