# Migration Status: aerisvault-old → AerisVault Monorepo

## Status: COMPLETE

The migration from the old monolithic `apps/aerisvault-old/` app to the new monorepo structure has been completed.

### Phase 1: DynaProcessing Library — DONE
All analysis modules have been migrated and rewritten to use the `Curve`-based API:

- [x] `statistics.py` — basic_statistics, peak_detection, settling_time, frequency_analysis, time_window_statistics
- [x] `event_detection.py` — detect_deployment, detect_inflation_phases, detect_steady_state, auto_detect_events
- [x] `comparison.py` — align_curves, calculate_rmse, calculate_difference, compare_statistics
- [x] `derivatives.py` — first_derivative, second_derivative
- [x] `filters.py` — added apply_savgol_filter
- [x] `curve.py` — added convenience methods (statistics, derivative, apply_savgol_filter)
- [x] `__init__.py` — all new modules exported in public API
- [x] 100+ automated tests covering all modules

### Phase 2: AerisVault UI App — DONE
The UI has been built as a thin shell delegating all computation to `dynaprocessing`:

- [x] `core/models.py` — SQLAlchemy ORM (Simulation, File, Tag)
- [x] `core/database.py` — CRUD operations with proper session management
- [x] `core/storage.py` — File upload, auto .dat/.csv → .parquet conversion
- [x] `core/config.py` — JSON-based configuration
- [x] `app.py` — Dashboard with overview and navigation
- [x] `pages/01_database.py` — Registry, upload, tagging
- [x] `pages/02_single_analysis.py` — Filtering, analysis, event detection, plotting
- [x] `pages/03_comparison.py` — Multi-simulation comparison with RMSE
- [x] `pages/04_settings.py` — Filter and plot configuration
- [x] `ui/components.py` — Reusable Streamlit widgets

### Not Yet Implemented
- [ ] DynaPrep library (pre-processor for generating LS-DYNA input decks)
- [ ] Report generation (PDF export of analysis results)
- [ ] Data export to formats other than Parquet
