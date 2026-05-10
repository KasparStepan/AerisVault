# AerisVault Aircraft CFD App Description

## Overview

This document describes a proposed AerisVault module for managing, analyzing, and comparing steady external-aerodynamics CFD results for aircraft. The module is intended as a focused first version for ANSYS Fluent workflows in which one fixed CFD setup is used and the angle of attack is varied across multiple cases to build an aerodynamic polar.[1]

The app is designed as a structured engineering database rather than a simple plotting tool. It should connect aircraft reference data, CFD setup metadata, raw force and moment outputs, part-level aerodynamic contributions, derived coefficients, comparison tools, and later simulation-planning capabilities into one coherent system.[2][3]

The recommended implementation follows the existing AerisVault philosophy: keep the analytical logic in a reusable library and keep the Streamlit UI thin. The current repository already separates computational engines from the user-facing app, and that same pattern should be reused here.

## Purpose

The purpose of the app is to manage aircraft external-aerodynamics CFD campaigns in a way that is practical for engineering work. In the first version, the app should support one aircraft, one fixed operating condition, and multiple angle-of-attack cases that together form one aerodynamic polar.[2][1]

The app should help answer questions such as:

- What are the aerodynamic characteristics of a given aircraft under a given CFD setup?
- How do lift, drag, and pitching-moment trends vary with angle of attack?
- How much do different aircraft parts contribute to the total loads?
- How do two operating conditions or two aircraft compare?
- Which simulations are planned, running, completed, or still missing from the database?[3][4]

## Scope of Version 1

The first version should remain intentionally narrow. It should focus on steady aircraft CFD polars built from a fixed Fluent setup where the angle of attack is varied and the rest of the boundary-condition definition remains the same.[1]

Version 1 should include:

- Aircraft definitions with aerodynamic reference values.
- User-defined CFD parts and engineering groups.
- Operating-condition records that describe one fixed Fluent setup.
- Multiple alpha cases inside each operating condition.
- Raw force and moment storage from CFD.
- Coefficient computation inside the app/library.
- Manual storage of selected pitching-moment coefficient curves for several CG positions, if desired for the first implementation.
- Plotting, comparison, and export tools.[5][6][3]

Version 1 should explicitly avoid over-generalization. It does not need to handle sideslip, control-surface matrices, automated cluster integration, full uncertainty quantification, or generalized arbitrary-axis aerodynamic database generation yet.[3][4]

## Design Principles

### Raw loads as source data

The strongest architectural choice for this module is to store raw CFD loads and compute derived aerodynamic quantities later. Force and moment coefficients depend on dynamic pressure and reference values, so storing only coefficients would make the database more fragile if those definitions ever change.[7][5][6]

The preferred source quantities are the force and moment components reported by Fluent in a fixed axis system. These raw values are closer to the true CFD output and are easier to recompute into lift, drag, side force, and aerodynamic coefficients later.[5][8]

### Fixed CFD axes, derived aerodynamic axes

The CFD workflow should use one fixed reporting convention for forces and moments, such as X, Y, and Z directions in a chosen body or solver axis system. The app should then rotate those raw loads into aerodynamic directions for each angle of attack, rather than redefining lift and drag directions in Fluent every time the boundary-condition direction changes.[9][10]

This keeps the CFD setup simpler and ensures that all runs use consistent report definitions. It also makes the post-processing system more robust because lift and drag become derived outputs rather than primary stored data.[9][11]

#### Concrete convention used in this project

The Fluent setup is fixed: force and moment reports are always in body axes, regardless of α. Only α changes between cases. The convention is:

- **x = forward, z = up, right-handed coordinate system**, which means y points to the **left**.
- **α positive = nose up** (standard aerospace).

The library performs the body-to-wind rotation per case (2D, no sideslip):

```
D =  Fx · cos(α) + Fz · sin(α)
L = -Fx · sin(α) + Fz · cos(α)
```

**Pitching-moment sign flip.** With y pointing left, Fluent's right-hand-rule My is nose-down positive, opposite to the aerospace Cm convention (nose-up positive). The library therefore applies:

```
My_aero = -My_fluent
```

before computing Cm. This sign flip lives in the library, not in Fluent reports.

A unit test must pin this down with a hand-checked case (e.g. a stable airfoil at moderate α must yield negative Cm about its MAC after the flip). Any future change to this convention is a breaking change, since every stored polar depends on it.

### Single-user posture

The module is used only by Stepan, not by a team. This relaxes coordination concerns (no auth, no audit logs, no migration safety nets sized for multiple users) but does **not** relax correctness concerns. Sign errors, unit mismatches, and axis-convention mistakes bite single users just as hard as teams, so they are still locked down in code with tests.

For mutable-state hazards where coordination matters more than correctness — e.g. editing `S_ref` on an aircraft after polars are computed, or changing reference values mid-campaign — a clear non-blocking warning in the UI is sufficient. Full snapshotting or freeze-on-publish is overkill for v1.

### Library-first architecture

The module should mirror the current AerisVault pattern where the library performs the domain calculations and the UI only orchestrates them. The repository already uses this separation for LS-DYNA post-processing, with the computational logic in `libs/dynaprocessing/` and the UI in `apps/aerisvault-ui/`.

The new module should therefore be split into:

- `libs/aerocfd/` for aerodynamic data structures, calculations, grouping logic, and plotting helpers.
- `apps/aerocfd-ui/` for Streamlit pages and user interactions.

## Monorepo Placement

The proposed new module should live in the AerisVault monorepo alongside the existing libraries and apps. The current repository already contains the top-level structure for reusable libraries and user-facing applications.

A recommended placement is:

```text
AerisVault/
├── libs/
│   ├── dynaprocessing/
│   └── aerocfd/
├── apps/
│   ├── aerisvault-ui/
│   └── aerocfd-ui/
```

This keeps the aircraft CFD work aligned with the broader AerisVault architecture and makes it easier to reuse shared database, storage, and UI ideas later.

## Core Domain Model

### Aircraft

The aircraft is the master object in the database. It provides the reference values and structural organization needed to interpret all results correctly.

An aircraft record should store:

- Name and description.
- Reference area `S_ref`.
- Reference chord `c_ref`, ideally MAC.
- Reference span `b_ref`.
- Axis and sign convention metadata.
- Optional CG presets or CG range.
- Defined CFD parts.
- Defined engineering groups.[6]

This is similar in spirit to the existing `Simulation` model in AerisVault, which already stores metadata such as velocity, reference area, air density, and mass so that raw results can be interpreted correctly.

### OperatingCondition

The operating condition is the second-level object and represents one fixed CFD setup. It is not a single point in the aerodynamic sense; rather, it is a coherent condition set under which several angle-of-attack cases are solved.

An operating condition should store:

- Name and description.
- Freestream velocity.
- Density, pressure, and/or altitude definition.
- Turbulence model.
- Turbulence boundary-condition definition.
- Optional mesh or solver notes.
- Links to all alpha cases.[1][4]

This matches the intended workflow in which one Fluent setup remains fixed and only angle of attack changes between cases.

### AlphaCase

Each alpha case is one solved CFD condition inside an operating condition. A collection of alpha cases forms the aerodynamic polar.

An alpha case should store:

- Angle of attack.
- Optional case label.
- Convergence status.
- Iteration count.
- Notes.
- Linked files.
- Raw total loads and/or part-level loads.
- Optional manually entered pitching-moment coefficient values for selected CG positions.

This object is the atomic result unit for the app.[1]

## Parts and Groups

### Aircraft parts

The app should allow the user to define CFD parts at the aircraft level. These are the raw extraction zones used in Fluent, such as wing, slot, trailing edge, fuselage front, fuselage rear, tailplane, or vertical tail.

These parts are properties of the aircraft CFD partitioning, not of a particular operating condition. Defining them once at the aircraft level ensures consistency across all operating conditions and alpha cases for that aircraft.[12][3]

### Engineering groups

The app should also allow grouping parts into larger engineering assemblies such as wing system, fuselage, tail, or total aircraft. Groups are analysis-facing abstractions that make it easier to interpret and compare aerodynamic contributions.[12][1]

Examples:

- `wing_system = wing + slot + trailing_edge`
- `fuselage = fuselage_front + fuselage_rear`
- `aircraft_total = all parts`

This grouping system is particularly valuable for drag breakdowns, load interpretation, and design iteration.

### Additivity rule

Forces and moments are the natural additive quantities, so grouping and summation should happen on raw loads rather than on already-computed coefficients. The app should sum raw part loads, then compute total or grouped coefficients using the aircraft reference values.[7][5]

## Data Strategy

### Raw force and moment storage

The preferred v1 storage format for each alpha case and each part is the fixed-axis force and moment vector:

- `Fx_N`
- `Fy_N`
- `Fz_N`
- `Mx_Nm`
- `My_Nm`
- `Mz_Nm`

This gives the app enough information to later compute lift, drag, side force, and relevant moments after applying the chosen axis transformation.[9][10]

### Derived quantities

The following should be computed in the library rather than stored as source data:

- Lift and drag.
- Side force.
- Lift, drag, and side-force coefficients.
- Lift-to-drag ratio.
- Group totals.
- Plot-ready aerodynamic polar data.[13][7][14]

### Pitching-moment handling: two paths, both kept

The module supports two coexisting paths for pitching-moment data, not one replacing the other.

**Path A — Manual Cm entry at selected CG positions (used in v1).** Stepan reads Cm values directly from Ansys at chosen CG positions (e.g. 20%, 25%, 30% MAC) and enters them into the app. This matches the current Fluent post-processing workflow and is the path that will actually be used first.

**Path B — Analytical moment transfer (lights up later).** When per-part surface centers (moment reference points) become available from Fluent, the library computes Cm at any CG by transferring raw moments through `M_cg = M_ref + r × F`. No schema migration is required to enable this — see *Database Design* below for the prepared fields.

Both paths remain available once Path B is enabled. They can be plotted side by side as a sanity check. Every stored Cm value carries a `source` tag (`manual` or `derived`) so plots and exports show its origin.

## Database Design

The existing AerisVault app already uses SQLAlchemy ORM models for simulations, files, tags, and many-to-many relationships, so the aircraft-CFD module should follow the same approach.

A recommended conceptual schema is described below.

### Aircraft tables

#### `aircraft`
Stores aircraft-level metadata and aerodynamic references.

Suggested fields:

- `id`
- `name`
- `description`
- `s_ref_m2`
- `c_ref_m`
- `b_ref_m`
- `axis_convention`
- `sign_convention`
- `created_at`

#### `aircraft_part`
Defines one CFD extraction zone for a given aircraft.

Suggested fields:

- `id`
- `aircraft_id`
- `name`
- `description`
- `display_order`
- `moment_ref_x_m` *(optional, NULL until surface centers are exported from Fluent — required for analytical Cm transfer, Path B)*
- `moment_ref_y_m` *(optional)*
- `moment_ref_z_m` *(optional)*

#### `aircraft_part_group`
Defines one engineering group for a given aircraft.

Suggested fields:

- `id`
- `aircraft_id`
- `name`
- `description`

#### `aircraft_part_group_member`
Maps parts into groups.

Suggested fields:

- `group_id`
- `part_id`

### Operating-condition table

#### `operating_condition`
Stores one fixed CFD setup for an aircraft.

Suggested fields:

- `id`
- `aircraft_id`
- `name`
- `description`
- `velocity_mps`
- `density_kgpm3`
- `pressure_pa`
- `altitude_m`
- `turbulence_model`
- `turbulence_bc_method`
- `turbulence_intensity_pct`
- `turbulent_viscosity_ratio`
- `notes`

### Result tables

#### `alpha_case`
One angle-of-attack case under one operating condition.

Suggested fields:

- `id`
- `operating_condition_id`
- `alpha_deg`
- `case_name`
- `convergence_status` *(enum, see below)*
- `iteration_count`
- `notes`

**`convergence_status` enum values:**

- `converged` — residuals and monitors are flat
- `partially_converged` — residuals dropped but monitors still drifting (usable but flagged in plots)
- `oscillating` — bounded oscillation, mean is meaningful
- `diverged` — solution blew up
- `stopped_manually` — killed before convergence
- `unknown` — not yet assessed

The same enum pattern (predefined string values, not free text) should be reused for the future `simtracker-ui` job statuses.

#### `alpha_case_part_load`
Stores part-level raw loads for one alpha case. **Every alpha case has part-level loads; there is no totals-only path.** Total and group loads are derived in the library by summing parts (the additivity rule), never stored.

Suggested fields:

- `id`
- `alpha_case_id`
- `part_id`
- `fx_n`
- `fy_n`
- `fz_n`
- `mx_nm`
- `my_nm`
- `mz_nm`

#### `alpha_case_manual_cm`
Stores pitching-moment coefficient values for selected CG positions. Used by Path A in v1 (manual entry from Ansys); analytically derived values from Path B can also be stored here, distinguished by the `source` field.

Suggested fields:

- `id`
- `alpha_case_id`
- `cg_over_mac`
- `cm_value`
- `source` — `manual` or `derived` (so plots/exports can show which path produced each curve)
- `source_label` *(optional free-text note, e.g. "from fluent report 2026-04-12")*

### Shared-support tables

The current AerisVault app already uses tags and file metadata. Those concepts should be reused to make the aircraft-CFD module searchable and attachable to source files, reports, and notes.

## File Management

The current AerisVault storage layer already handles raw and processed files via a `StorageManager`, creating `raw/` and `processed/` subdirectories and linking files to entities in the database.

The aircraft-CFD module should reuse the same design philosophy. Files that may be attached include:

- Fluent report files.
- CSV result tables.
- Residual plots.
- Screenshots.
- Journal files.
- Setup notes.

For v1, file support should remain simple:

- attach files,
- keep their metadata,
- optionally import CSV data.

Heavy parser automation can be added later.

## UI Design

The Streamlit app should be structured into pages, similar to the current AerisVault UI, which already separates concerns into pages for database management, analysis, comparison, and settings.

A recommended page layout is described below.

### Aircraft page

Purpose:
- Create and edit aircraft.
- Set aerodynamic reference values.
- Define CFD parts.
- Define engineering groups.
- Define CG presets or notes.

### Operating Conditions page

Purpose:
- Create and edit operating conditions for a selected aircraft.
- Record Fluent setup metadata.

### Data Entry page

Purpose:
- Add alpha cases.
- Enter total or part-level loads.
- Enter manual `Cm` values for selected CG positions.
- Import CSV tables.
- Attach files.

### Analysis page

Purpose:
- Show all figures for one selected aircraft and operating condition.

Recommended figures:

- `CL-alpha`
- `CD-alpha`
- `L/D-alpha`
- `CL-CD` polar
- `Cm-alpha` with multiple CG curves
- optional part/group contribution plots

This figure set matches the intended user workflow for inspecting one aerodynamic dataset.[2][1]

### Comparison page

Purpose:
- Compare multiple operating conditions or multiple aircraft.

### Settings page

Purpose:
- Manage tags.
- Manage conventions.
- Manage import behavior.
- Hold future advanced settings.

## Analysis Features

The library should provide the following analytical capabilities:

- Rotation of fixed-axis loads into aerodynamic directions for each angle of attack.
- Coefficient calculation using aircraft reference values and operating-condition freestream parameters.
- Summation from part level to group level to total-aircraft level.
- Generation of plot-ready datasets.
- Export of processed tables to CSV.
- Support for plotting multiple `Cm(alpha)` curves corresponding to different CG positions.[9][10][1]

This is analogous to how the current `dynaprocessing` library provides filtering, statistics, event detection, and plotting helpers for the existing AerisVault UI.

## Comparator Module

The comparison module should be part of version 1 because comparison is one of the main reasons to build a structured aerodynamic database. Aerodynamic databases are most useful when they allow direct comparison between configurations, conditions, and datasets under consistent conventions.[2][1]

### Use cases

The comparison module should support:

- Comparison of two operating conditions for the same aircraft.
- Comparison of two aircraft under similar operating conditions.
- Comparison of group-level contributions such as wing, fuselage, and tail.
- Export of comparison data to CSV.

### Comparison views

Recommended views include:

- Overlayed `CL-alpha` curves.
- Overlayed `CD-alpha` curves.
- Overlayed `L/D-alpha` curves.
- Overlayed `CL-CD` polars.
- Overlayed `Cm-alpha` curves for matching CG definitions.
- Tabular delta summaries at common alpha points.

In version 1, the natural comparison object should be the operating condition, because it represents a full aerodynamic polar dataset rather than a single isolated CFD case.

## Simulation Planning and Tracking

The simulation-planning capability should be implemented as a separate but linked AerisVault app rather than being embedded directly inside the aircraft-CFD module. CFD workflow-management systems are most effective when they centralize job status, metadata, and links to results across projects.[3][4]

### Recommended separate app

A suitable future app name is:

- `apps/simtracker-ui/`

### Purpose

The planning/tracking app should help manage:

- Planned CFD runs.
- In-progress simulations.
- Completed jobs waiting for post-processing.
- Failed runs.
- Links from jobs to stored aerodynamic datasets.

### Suggested simulation-job model

A simulation-job object should store:

- Job name.
- Linked aircraft or project.
- Solver.
- Status.
- Priority.
- Planned start/finish.
- Actual run timing.
- Notes.
- Link to output dataset.

### Suggested statuses

- `planned`
- `setup`
- `queued`
- `running`
- `post_processing`
- `done`
- `failed`

This app should be solver-agnostic so it can later serve both aircraft CFD and other AerisVault domains such as parachute CFD/FSI.[3]

## Management and Search

Long-term usability depends on strong management and search features. Once the number of operating conditions grows, the app must help users find datasets by engineering meaning rather than by folder names alone.[3][4]

Useful searchable metadata includes:

- Aircraft name.
- Operating-condition name.
- Velocity range.
- Turbulence model.
- Density or altitude.
- Tags.
- Notes.
- Available groups or parts.

The current AerisVault system already uses tags and file relationships, which should be reused here for consistency.

## Data Entry Strategy

For the first version, the system should support three practical input modes:

- Manual entry of a single alpha case.
- Table-style entry of several alpha cases.
- CSV import for bulk loading.

This is more realistic and more maintainable than requiring immediate full automation of Fluent parsing. The internal schema should be defined first, then importers can be layered on top.[3][4]

A typical workflow should be:

1. Create the aircraft.
2. Define the parts and groups.
3. Create the operating condition.
4. Add alpha cases.
5. Enter or import raw loads.
6. Enter manual `Cm` data if needed.
7. Review plots and export results.

## Deferred Features

To protect the quality of version 1, several features should be deliberately deferred:

- Full analytical moment transfer from a single reference point to arbitrary CG locations.
- Sideslip and full 3D aerodynamic-database generation.
- Control-surface deflection sweeps.
- Mesh-convergence and uncertainty analysis workflows.
- Automatic Fluent parser generation.
- Cluster scheduler integration.
- Automated report generation.

These features are valuable but should not be allowed to block the first useful release.[3][4]

## Development Roadmap

A practical implementation order is:

### Phase 1: Library foundation

Build `libs/aerocfd/` with:

- Data structures.
- Load transformation logic.
- Coefficient calculations.
- Grouping logic.
- Plot-data preparation.

### Phase 2: Database and ORM

Add SQLAlchemy models for:

- Aircraft.
- Parts.
- Groups.
- Operating conditions.
- Alpha cases.
- Part loads.
- Manual CG moment data.

### Phase 3: Management UI

Create Streamlit pages for:

- Aircraft management.
- Operating-condition management.
- Data entry.

### Phase 4: Analysis UI

Implement:

- Main plots.
- Contribution plots.
- Exports.

### Phase 5: Comparison UI

Implement:

- Overlay comparisons.
- Delta tables.
- Comparison exports.

### Phase 6: Planning app

Build the separate simulation-planning/tracking app and link it back to the stored datasets.[3]

## Summary

The proposed aircraft-CFD app is a strong extension of AerisVault. It is best understood as a structured aerodynamic database and analysis environment for steady external-aerodynamics CFD, not merely a plot viewer. It should organize aircraft definitions, operating conditions, alpha-case results, raw loads, part breakdowns, comparison tools, and eventually campaign planning into one coherent engineering workflow.[2][1][3]

The key architectural decisions are:

- Use `Aircraft -> OperatingCondition -> AlphaCase` as the backbone.
- Define CFD parts and engineering groups at the aircraft level.
- Store raw loads and compute coefficients in the library.
- Support simple manual `Cm(alpha)` data for selected CG values in version 1.
- Treat the operating condition as the natural comparison unit.
- Build simulation planning as a separate linked AerisVault app.[3]

That design is focused enough to build now and flexible enough to expand later.