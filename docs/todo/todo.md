Migration Plan: 
aerisvault-old
 → AerisVault Monorepo
Problem
The old 
apps/aerisvault-old/
 package is a monolithic Streamlit app that mixes library-level computation (parsers, filters, analysis, physics) with UI-level code (pages, plotting, database, storage). The current monorepo already has a well-structured dynaprocessing library with proper 
Curve
-based API, but:

Several analysis modules exist only in the old app and need to be migrated to dynaprocessing
The aerisvault-ui app is completely empty (stub files) and needs to be built as the thin UI shell
The old code uses raw pd.DataFrame columns as its data model — the new code uses immutable 
Curve
 objects. We need to bridge this paradigm shift cleanly.
User Review Required
IMPORTANT

Design Decision — Curve-centric analysis API The old code's analysis modules (
StatisticalAnalyzer
, 
EventDetector
, etc.) all operate on raw pd.DataFrame with hardcoded column names like 'Fpz'. The proposed approach is to rewrite them to operate on 
Curve
 objects instead, adding convenience methods directly to the 
Curve
 class where it makes sense (e.g., curve.statistics(), curve.derivative()). For multi-curve analyses (comparison, convergence), we keep standalone functions that accept List[Curve]. This keeps the library clean and Pythonic.

IMPORTANT

Scope question — Do you want all the old features migrated, or only the core ones? The old app has several features of varying importance:

Core (high value): Analysis (statistics, event detection, CdS calculation), visualization, DB management
Medium value: Comparison analysis, report generation, export
Low value, may be outdated: Settings page with JSON persistence, some plotting subplots
I recommend starting with Phase 1 (library) first, which is the most important and well-defined. Phase 2 (UI) can be done incrementally afterward.

Analysis: What Already Exists vs What's Missing
✅ Already in dynaprocessing (no migration needed)
Feature	Old File	Current Location
LS-DYNA CSV parser	
parsers.py
io/lsdyna_csv.py
 (improved, 
Curve
-based)
LS-DYNA DAT parser	
parsers.py
io/lsdyna_csv.py
 (improved, Z-inversion)
Butterworth filter	
filters.py
analysis/filters.py
 (pure functions)
Moving average	
filters.py
analysis/filters.py
SAE CFC filter	(not in old)	
analysis/filters.py
 (new!)
Curve model	(DataFrame-based)	
models/curve.py
 (immutable, 286 lines)
Simulation models	(none)	
models/simulation.py
, 
finite_mass.py
, 
infinite_mass.py
Drag coefficient calc	
physics.py
, 
analysis/drag_coefficient.py
Curve.calculate_drag_coefficient()
Job pipeline	(none)	
analysis/postprocess.py
Plotly viz	
plotting/single_plot.py
viz/plot_utils.py
 (Curve-based)
Matplotlib viz	(none)	
viz/plot_utils.py
Tests	(none)	4 test files, 534 lines
❌ Missing — needs migration to dynaprocessing
Feature	Old File	Lines	Priority
Statistical analysis (basic stats, peaks, settling, FFT, correlation)	
analysis/statistics.py
225	High
Event detection (deployment, inflation, steady-state, oscillations)	
analysis/event_detection.py
238	High
Derivatives (1st, 2nd order)	
analysis/derivatives.py
110	Medium
Simulation comparison (align, RMSE, differences)	
analysis/comparison.py
122	Medium
Savitzky-Golay filter	
filters.py
25	Medium
❌ Missing — needs migration to aerisvault-ui
Feature	Old File	Lines	Priority
Database ORM models	
models.py
102	High
Database manager	
database.py
238	High
Storage manager	
storage.py
93	High
Config management	
config.py
81	Medium
Main app	
app.py
74	High
Database page	
pages/1_database.py
, 
ui/pages.py
606	High
Analysis page	
pages/2_single_analysis.py
526	High
Comparison page	
pages/3_comparison.py
67	Medium
Report generator	
reports/generator.py
180	Low
Data exporter	
export.py
32	Low
Proposed Changes
Phase 1: Enrich dynaprocessing Library
The analysis modules from the old app contain real engineering value (peak detection, event detection, FFT, CdS analysis). These must live in the library, not the UI.

[NEW] 
statistics.py
Port 
StatisticalAnalyzer
 to work with 
Curve
 objects:

basic_statistics(curve) → dict
 — mean, std, min, max, RMS
peak_detection(curve, prominence, distance) → dict
 — using scipy.signal.find_peaks
settling_time(curve, tolerance) → dict
frequency_analysis(curve, num_frequencies) → dict
 — FFT
time_window_statistics(curve, t_start, t_end) → dict
Add convenience method to 
Curve
:

Curve.statistics() → dict
[NEW] 
event_detection.py
Port 
EventDetector
 to work with 
Curve
 objects:

detect_deployment(curve, threshold_factor) → dict
detect_inflation_phases(curve) → dict
detect_steady_state(curve, tolerance, window) → dict
detect_oscillations(curve, min_freq, max_freq) → dict
auto_detect_events(curve) → dict
[NEW] 
comparison.py
Port 
SimulationComparator
 to work with 
Curve
 objects:

align_curves(curves: List[Curve]) → List[Curve]
calculate_rmse(curve_a, curve_b) → float
calculate_difference(curve_a, curve_b) → Curve
compare_statistics(curves: List[Curve]) → pd.DataFrame
[NEW] 
derivatives.py
Port 
DerivativeCalculator
 to return 
Curve
 objects:

first_derivative(curve, smooth) → Curve
second_derivative(curve, smooth) → Curve
Add convenience method:

Curve.derivative(order=1) → Curve
[MODIFY] 
filters.py
Add apply_savgol_filter() function and corresponding Curve.apply_savgol_filter() method. The old code uses this extensively.

[MODIFY] 
curve.py
Add convenience methods:

statistics() → dict
derivative(order=1) → Curve
apply_savgol_filter(window_length, polyorder) → Curve
[MODIFY] 
__init__.py
Export new analysis modules in the public API.

Phase 2: Build aerisvault-ui App (Thin UI Shell)
The UI app should only handle Streamlit rendering, session state, and database operations. All computation is delegated to dynaprocessing.

Key design changes from old app:
Rewire analysis pages to use 
Curve
 objects from dynaprocessing instead of raw DataFrames
Use dynaprocessing.viz.plot_curves_plotly() instead of the old 
SinglePlotter
 class (which mixed config with plotting)
Keep database/storage/config in the UI app — these are app-level concerns, not library concerns
[NEW] App directory structure
apps/aerisvault-ui/
├── pyproject.toml
├── README.md
└── src/aerisvault/
    ├── app.py                 # Main entry, dashboard
    ├── core/
    │   ├── __init__.py
    │   ├── config.py          # From old config.py
    │   ├── database.py        # From old database.py
    │   ├── models.py          # From old models.py (ORM)
    │   └── storage.py         # From old storage.py
    ├── ui/
    │   ├── __init__.py
    │   └── components.py      # Reusable Streamlit widgets
    └── pages/
        ├── 01_database.py
        ├── 02_single_analysis.py
        ├── 03_comparison.py
        └── 04_settings.py
[NEW] 
pyproject.toml
Declare dependencies: streamlit, sqlalchemy, 
plotly
, dynaprocessing (editable).

[NEW] Core modules (port from old with minimal changes)
core/models.py — Direct copy of SQLAlchemy ORM models
core/database.py — Direct copy with imports adjusted
core/storage.py — Adjusted to use dynaprocessing.io parsers instead of old one
core/config.py — Adjusted paths for monorepo layout
[NEW] Pages (rewired to use dynaprocessing)
pages/02_single_analysis.py — The biggest rewrite. Instead of using raw DataFrames and old 
DataFilter
/
SinglePlotter
, it will:
Load data via 
InfiniteMassSimulation
 or 
FiniteMassSimulation
Get 
Curve
 objects
Apply filters via curve.apply_cfc_filter() / curve.apply_butterworth_filter()
Plot via dynaprocessing.viz.plot_curves_plotly()
Run analysis via dynaprocessing.analysis.statistics / event_detection
Verification Plan
Automated Tests
All tests run from the dynaprocessing library root:

bash
cd /home/stepan/projects/PhD/AerisVault/libs/dynaprocessing
python -m pytest tests/ -v
Existing tests (must still pass):
tests/test_curve.py
 — 14 tests covering Curve construction, immutability, filtering, unit conversion, Cd, export
tests/test_filters.py
 — 10 tests covering CFC, Butterworth, moving average
tests/test_parsers.py
 — 10 tests covering CSV and DAT parsing
tests/test_metadata.py
 — 6 tests covering directory name metadata extraction
New tests to write:
tests/test_statistics.py — Test 
basic_statistics()
, 
peak_detection()
, 
settling_time()
, 
frequency_analysis()
tests/test_event_detection.py — Test 
detect_deployment()
, 
detect_steady_state()
 with synthetic force profiles
tests/test_comparison.py — Test align_curves(), 
calculate_rmse()
 with known expected values
tests/test_derivatives.py — Test 
first_derivative()
, 
second_derivative()
 against known analytical derivatives
Manual Verification
Streamlit smoke test: After Phase 2, run cd apps/aerisvault-ui && streamlit run src/aerisvault/app.py and verify the dashboard loads without errors
Could you test the UI pages manually? — Upload a .dat file in the database page, navigate to single analysis, verify plots render correctly. I'm not sure if you have test .dat files available — please let me know.
