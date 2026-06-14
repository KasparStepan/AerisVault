# dynaprocessing Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the correctness nits, unify the simulation API, and prepare `dynaprocessing` for clean publishing — without changing its good core design.

**Architecture:** `dynaprocessing` stays a pure, headless, immutable-`Curve` library. This plan tightens correctness (CFC standard compliance, divide-by-zero), makes the two simulation models expose a uniform curve-access interface, splits heavy plotting deps into optional extras, closes the Parquet round-trip, and hardens two detectors. No rewrite.

**Tech Stack:** Python 3.10+, NumPy, SciPy, Pandas, pytest. Optional: Plotly, Matplotlib, PyArrow.

**Reference:** review findings in this session (P1/P2/P3 priority table).

> **✅ STATUS: COMPLETED (2026-06-14).** All 8 tasks executed on branch `dynaprocessing-refinement` (merged to `main`), TDD throughout, 139 tests passing (was 126; +13). Two deviations from the plan as written, both intentional and reflected below:
> - **Task 5 version:** the four pyprojects were already aligned at `0.1.0` (the only mismatch was a hardcoded `v0.3.0` banner in `app.py`), so the bump was to **`0.2.0`** (honest next-minor) rather than the plan's arbitrary `0.4.0`; the banner was fixed too.
> - **Task 8 test:** a single duplicate timestamp did not skew the mean enough to fail, so the test was strengthened to a 50-stamp duplicate block (`test_robust_to_duplicate_timestamp_block`) that genuinely discriminates median-vs-mean.
> - **Task 4 lazy-import guard** already passed (the package `__init__` never imported viz); matplotlib was still made lazy inside `viz` and the guard kept as a regression test.

**Environment:** all commands use the project venv and run from the library root:
```
cd /home/stepan/projects/PhD/AerisVault/libs/dynaprocessing
/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -q
```

---

## Phasing

- **Phase 1 (P1) — correctness:** Tasks 1–3. Do these alongside the FSI migration; they touch code that migration consumes.
- **Phase 2 (P2) — packaging & round-trip:** Tasks 4–6. Cheap, enable publishing.
- **Phase 3 (P3) — hardening:** Tasks 7–8.
- **Deferred (separate plan):** dataclass return types for detectors, viz web/report file split, metadata-from-directory decoupling, FFT logic de-duplication. Rationale in the final section — these are a structural refactor cycle of their own.

---

## Task 1: Fix divide-by-zero in `calculate_cds_from_velocity`

**Files:**
- Modify: `src/dynaprocessing/models/curve.py:325-346`
- Test: `tests/test_physics.py`

The current `np.where(...)` evaluates the division on *every* element, including where velocity ≈ 0, emitting `RuntimeWarning: divide by zero` (confirmed in the test run). The selected result is already NaN; we just need to suppress the spurious division.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_physics.py` inside `class TestCalculateCdSFromVelocity`:

```python
    def test_no_divide_by_zero_warning(self, force_curve):
        """Velocity reaching zero must not emit a RuntimeWarning."""
        import warnings

        t = np.linspace(0, 1, 100)
        v_to_zero = np.linspace(10, 0, 100)
        vel = Curve(time=t, values=v_to_zero, name="v")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            cds = force_curve.calculate_cds_from_velocity(vel)

        runtime_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
        assert not runtime_warnings, f"unexpected RuntimeWarning(s): {[str(w.message) for w in runtime_warnings]}"
        assert np.isnan(cds.values[-1])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_physics.py::TestCalculateCdSFromVelocity::test_no_divide_by_zero_warning -v`
Expected: FAIL — a `RuntimeWarning: divide by zero` is captured.

- [ ] **Step 3: Fix the implementation**

In `src/dynaprocessing/models/curve.py`, replace the body of `calculate_cds_from_velocity` from the `v_squared = ...` line through the `cds_values = np.where(...)` block with:

```python
        velocity_values = velocity_curve.values
        near_zero = np.abs(velocity_values) <= 0.1
        dynamic_pressure = 0.5 * rho * velocity_values ** 2

        # CdS is physically undefined when the payload is nearly stationary.
        # Suppress the divide-by-zero from the masked-out elements; np.where
        # discards them anyway, but it still evaluates the division eagerly.
        with np.errstate(divide="ignore", invalid="ignore"):
            cds_values = np.where(
                near_zero,
                np.nan,
                self._values / dynamic_pressure,
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_physics.py -v`
Expected: all `TestCalculateCdSFromVelocity` tests pass, no warnings.

- [ ] **Step 5: Commit**

```bash
git add src/dynaprocessing/models/curve.py tests/test_physics.py
git commit -m "fix: suppress divide-by-zero in calculate_cds_from_velocity"
```

---

## Task 2: Make the CFC filter SAE J211-compliant (2nd-order, phaseless)

> **DECISION REQUIRED (results-affecting):** SAE J211 specifies a **2nd-order** Butterworth applied forward+backward. The current code uses **4th-order** ([filters.py:73](../../../libs/dynaprocessing/src/dynaprocessing/analysis/filters.py#L73)), which over-attenuates. This task implements the standard 2nd-order form. **This changes every CFC-filtered result.** If Stepan has already reported CFC-filtered loads with the 4th-order version, confirm before merging — either adopt the standard (recommended) or keep 4th-order and document it as a deliberate deviation.

**Files:**
- Modify: `src/dynaprocessing/analysis/filters.py:41-74`
- Test: `tests/test_filters.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_filters.py` inside `class TestCFCFilter`:

```python
    def test_matches_second_order_phaseless_butterworth(self):
        """SAE J211 CFC = 2nd-order Butterworth applied forward+backward at fc = CFC*5/3."""
        from scipy import signal

        fs = 10000
        t = np.linspace(0, 1, fs)
        x = np.random.RandomState(0).randn(fs)

        out = apply_cfc_filter(t, x, cfc=60)

        fc = 60 * (5.0 / 3.0)
        nyq = 0.5 * fs
        b, a = signal.butter(2, fc / nyq, btype="low", analog=False)
        expected = signal.filtfilt(b, a, x)

        np.testing.assert_allclose(out, expected, rtol=1e-9, atol=1e-12)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_filters.py::TestCFCFilter::test_matches_second_order_phaseless_butterworth -v`
Expected: FAIL — output uses a 4th-order filter, not 2nd-order.

- [ ] **Step 3: Change the filter order to 2**

In `src/dynaprocessing/analysis/filters.py`, in `apply_cfc_filter`, change the Butterworth design line from order 4 to order 2 and update the docstring sentence:

```python
    # SAE J211 specifies a 2nd-order Butterworth applied forward and backward
    # (filtfilt) for zero phase distortion.
    b, a = signal.butter(2, normal_cutoff, btype="low", analog=False)
    return signal.filtfilt(b, a, data)
```

Also update the docstring line that currently says "4th-order Butterworth" to "2nd-order Butterworth applied forward and backward (filtfilt), per SAE J211".

- [ ] **Step 4: Run the full filter suite**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_filters.py -v`
Expected: all pass (the existing attenuation/DC tests still hold; the new coefficient-match test passes).

- [ ] **Step 5: Commit**

```bash
git add src/dynaprocessing/analysis/filters.py tests/test_filters.py
git commit -m "fix: CFC filter uses 2nd-order Butterworth per SAE J211"
```

---

## Task 3: Unify curve access across simulation types (`list_curves`)

**Files:**
- Modify: `src/dynaprocessing/models/simulation.py`
- Modify: `src/dynaprocessing/models/infinite_mass.py`
- Modify: `src/dynaprocessing/models/finite_mass.py`
- Test: `tests/test_simulation_interface.py` (new)

`InfiniteMassSimulation.curves` is `Dict[str, Curve]`; `FiniteMassSimulation.curves` is `Dict[str, Dict[str, Curve]]`. Both already have `get_curve(name)`. We add a uniform `list_curves() -> list[Curve]` so callers (the FSI module pages) never branch on the storage shape. `.curves` is left as-is (non-breaking).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_simulation_interface.py
"""The two simulation types must expose a uniform curve-access interface."""

from dynaprocessing.models.infinite_mass import InfiniteMassSimulation
from dynaprocessing.models.finite_mass import FiniteMassSimulation


def _write_infinite_mass_dat(directory):
    path = directory / "drag.dat"
    path.write_text(
        "time Fpx Fpy Fpz\n"
        "0.0 1.0 2.0 3.0\n"
        "0.1 1.1 2.1 3.1\n"
        "0.2 1.2 2.2 3.2\n"
    )
    return path


def _write_finite_mass_csv(directory):
    path = directory / "All_data.csv"
    path.write_text(
        "Time,z_acceleration@13513-,Time,z_velocity@13513-,\n"
        "0.0,10.0,0.0,5.0,\n"
        "0.1,11.0,0.1,5.1,\n"
        "0.2,12.0,0.2,5.2,\n"
    )
    return path


def test_infinite_mass_list_curves(tmp_path):
    sim_dir = tmp_path / "scrab_2m_40ms_folded"
    sim_dir.mkdir()
    _write_infinite_mass_dat(sim_dir)

    sim = InfiniteMassSimulation(directory_path=sim_dir)
    names = sorted(c.name for c in sim.list_curves())
    assert names == ["Fpx", "Fpy", "Fpz"]


def test_finite_mass_list_curves(tmp_path):
    sim_dir = tmp_path / "cross_2m_6kg_6ms"
    sim_dir.mkdir()
    _write_finite_mass_csv(sim_dir)

    sim = FiniteMassSimulation(directory_path=sim_dir)
    names = sorted(c.name for c in sim.list_curves())
    assert names == ["z_acceleration", "z_velocity"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_simulation_interface.py -v`
Expected: FAIL — `AttributeError: 'InfiniteMassSimulation' object has no attribute 'list_curves'`.

- [ ] **Step 3: Declare the interface on the base class**

In `src/dynaprocessing/models/simulation.py`, add to `BaseSimulation` (after `summary`):

```python
    def list_curves(self) -> "list":
        """Return all curves as a flat list, regardless of internal storage shape.

        Subclasses override this. Provides a uniform interface so callers never
        branch on whether curves are stored flat (infinite mass) or nested by
        node (finite mass).
        """
        raise NotImplementedError
```

- [ ] **Step 4: Implement on each subclass**

In `src/dynaprocessing/models/infinite_mass.py`, add to `InfiniteMassSimulation`:

```python
    def list_curves(self) -> List[Curve]:
        """All loaded curves (flat storage, one Curve per force/moment column)."""
        return list(self.curves.values())
```

In `src/dynaprocessing/models/finite_mass.py`, add to `FiniteMassSimulation`:

```python
    def list_curves(self) -> List[Curve]:
        """All loaded curves, flattened across nodes."""
        return [
            curve
            for node_curves in self.curves.values()
            for curve in node_curves.values()
        ]
```

(`List` and `Curve` are already imported in both files.)

- [ ] **Step 5: Run test to verify it passes**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_simulation_interface.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add src/dynaprocessing/models/simulation.py src/dynaprocessing/models/infinite_mass.py src/dynaprocessing/models/finite_mass.py tests/test_simulation_interface.py
git commit -m "feat: uniform list_curves() across simulation types"
```

---

## Task 4: Split heavy plotting deps into optional extras + lazy-import matplotlib

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/dynaprocessing/viz/plot_utils.py:14-15` (move matplotlib imports into functions)
- Test: `tests/test_lazy_imports.py` (new)

Core library should be `numpy/scipy/pandas` only. `plotly`, `matplotlib`, `pyarrow` become extras. The Plotly figure is already lazily imported; matplotlib is imported at module top and must become lazy so `import dynaprocessing` (and Plotly-only web use) never pulls a GUI stack.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_lazy_imports.py
"""Importing the core library must not pull in matplotlib."""

import subprocess
import sys


def test_core_import_does_not_pull_matplotlib():
    code = (
        "import sys, dynaprocessing; "
        "mods = [m for m in sys.modules if m.startswith('matplotlib')]; "
        "assert not mods, mods"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_lazy_imports.py -v`
Expected: FAIL — matplotlib is imported transitively via `viz/plot_utils.py` top-level import (which `dynaprocessing` does not import directly, but if it does through any chain it will surface here; if it already passes, keep the test as a guard and continue).

Note: `dynaprocessing/__init__.py` does not import `viz`, so this may already pass. If it passes at this step, that is fine — proceed to Step 3 to make the matplotlib import lazy *within viz* so `import dynaprocessing.viz.plot_utils` for Plotly use also avoids matplotlib, then keep the guard test.

- [ ] **Step 3: Make matplotlib imports lazy in viz**

In `src/dynaprocessing/viz/plot_utils.py`, remove the two top-level lines:

```python
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
```

Add `import matplotlib.pyplot as plt` as the first line inside `plot_curves`, and inside `export_pdf` add both:

```python
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
```

Change the `plot_curves` return annotation `Tuple[plt.Figure, plt.Axes]` to `Tuple["Any", "Any"]` (since `plt` is no longer module-level), keeping `Any` already imported from typing.

- [ ] **Step 4: Update pyproject dependencies and extras**

In `pyproject.toml`, replace the `dependencies` and `[project.optional-dependencies]` blocks with:

```toml
dependencies = [
    "numpy>=1.24",
    "pandas>=2.0",
    "scipy>=1.10",
]

[project.optional-dependencies]
viz = ["plotly>=5.15"]
report = ["matplotlib>=3.7"]
io = ["pyarrow>=12.0"]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "plotly>=5.15",
    "matplotlib>=3.7",
    "pyarrow>=12.0",
]
```

- [ ] **Step 5: Reinstall and run tests**

Run:
```bash
/home/stepan/projects/PhD/AerisVault/.venv/bin/pip install -e "libs/dynaprocessing[dev]"
cd libs/dynaprocessing && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -q
```
Expected: all tests pass (dev extra keeps matplotlib/plotly/pyarrow available for the test run); `test_lazy_imports` passes.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/dynaprocessing/viz/plot_utils.py tests/test_lazy_imports.py
git commit -m "refactor: optional viz/report/io extras, lazy matplotlib import"
```

---

## Task 5: Fix `Path` import and reconcile the unified version

**Files:**
- Modify: `src/dynaprocessing/models/curve.py`
- Modify: `pyproject.toml` (root), `libs/dynaprocessing/pyproject.toml`, `libs/dynaprep/pyproject.toml`, `apps/aerisvault-ui/pyproject.toml`

`curve.py` annotates `filepath: str | Path` ([curve.py:457](../../../libs/dynaprocessing/src/dynaprocessing/models/curve.py#L457)) but `Path` is only imported locally inside `to_parquet`. The four pyprojects are out of sync (lib `0.1.0`, app banner `0.3.0`).

- [ ] **Step 1: Import `Path` at module top in curve.py**

In `src/dynaprocessing/models/curve.py`, add to the imports block (near line 11):

```python
from pathlib import Path
```

In `to_parquet`, remove the local `from pathlib import Path as _Path` line and change `out = _Path(filepath).resolve()` to `out = Path(filepath).resolve()`.

- [ ] **Step 2: Verify import and parquet still work**

Run: `cd libs/dynaprocessing && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -q`
Expected: all pass.

- [ ] **Step 3: Reconcile the version to 0.2.0 across all four pyprojects**

Inspect each file's version:
```bash
cd /home/stepan/projects/PhD/AerisVault
grep -H "version" pyproject.toml libs/dynaprocessing/pyproject.toml libs/dynaprep/pyproject.toml apps/aerisvault-ui/pyproject.toml
```
Set the `version = "..."` line in all four to `version = "0.2.0"` (they were already aligned at `0.1.0`, so this is a normal next-minor bump marking the refactor). Also fix the hardcoded `v0.3.0` banner in `apps/aerisvault-ui/src/aerisvault/app.py`. (If the FSI-migration rename has already run, the app path is `apps/aerisvault/pyproject.toml` — adjust accordingly.)

- [ ] **Step 4: Reinstall and confirm**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/pip install -e libs/dynaprocessing`
Expected: `Successfully installed dynaprocessing-0.2.0`.

- [ ] **Step 5: Commit**

```bash
git add src/dynaprocessing/models/curve.py
git add pyproject.toml libs/dynaprocessing/pyproject.toml libs/dynaprep/pyproject.toml apps/aerisvault-ui/pyproject.toml
git commit -m "chore: import Path at module top; unify monorepo version to 0.2.0"
```

---

## Task 6: Close the Parquet round-trip (`Curve.from_dataframe` / `from_parquet`)

**Files:**
- Modify: `src/dynaprocessing/models/curve.py`
- Test: `tests/test_curve.py`

The library can write a `Curve` to Parquet but cannot read one back. The UI stores Parquet on ingest — these loaders let the FSI module reload quickly without re-parsing raw files.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_curve.py`:

```python
class TestCurveRoundTrip:
    def test_from_dataframe_single_value_column(self):
        import pandas as pd
        df = pd.DataFrame({"time": [0.0, 0.1, 0.2], "Fpz": [3.0, 3.1, 3.2]})
        curve = Curve.from_dataframe(df)
        assert curve.name == "Fpz"
        np.testing.assert_array_equal(curve.time, [0.0, 0.1, 0.2])
        np.testing.assert_array_equal(curve.values, [3.0, 3.1, 3.2])

    def test_from_dataframe_explicit_value_column(self):
        import pandas as pd
        df = pd.DataFrame({"t": [0.0, 1.0], "a": [9.0, 8.0], "b": [1.0, 2.0]})
        curve = Curve.from_dataframe(df, time_column="t", value_column="b")
        assert curve.name == "b"
        np.testing.assert_array_equal(curve.values, [1.0, 2.0])

    def test_from_dataframe_ambiguous_raises(self):
        import pandas as pd
        df = pd.DataFrame({"time": [0.0], "a": [1.0], "b": [2.0]})
        with pytest.raises(ValueError, match="value_column"):
            Curve.from_dataframe(df)

    def test_parquet_round_trip(self, tmp_path):
        t = np.linspace(0, 1, 50)
        original = Curve(time=t, values=np.sin(t), name="Fpz", units="N")
        path = original.to_parquet(tmp_path / "fpz.parquet")
        restored = Curve.from_parquet(path)
        assert restored.name == "Fpz"
        np.testing.assert_allclose(restored.time, original.time)
        np.testing.assert_allclose(restored.values, original.values)
```

(`numpy as np` and `pytest` are already imported at the top of `tests/test_curve.py`.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_curve.py::TestCurveRoundTrip -v`
Expected: FAIL — `AttributeError: type object 'Curve' has no attribute 'from_dataframe'`.

- [ ] **Step 3: Implement the classmethods**

In `src/dynaprocessing/models/curve.py`, add after `to_parquet`:

```python
    # ------------------------------------------------------------------
    # Import (classmethods)
    # ------------------------------------------------------------------
    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        *,
        time_column: str = "time",
        value_column: Optional[str] = None,
        **kwargs: Any,
    ) -> Curve:
        """Build a Curve from a two-column DataFrame.

        Args:
            df: Source DataFrame containing a time column and one value column.
            time_column: Name of the time column (default 'time').
            value_column: Name of the value column. If None, inferred as the
                single non-time column; raises if that is ambiguous.
            **kwargs: Extra Curve fields (units, node_id, metadata, ...).

        Raises:
            ValueError: If value_column is omitted and the DataFrame does not
                have exactly one non-time column.
        """
        if value_column is None:
            candidates = [c for c in df.columns if c != time_column]
            if len(candidates) != 1:
                raise ValueError(
                    f"Cannot infer value_column from columns {list(df.columns)}; "
                    f"pass value_column explicitly."
                )
            value_column = candidates[0]

        return cls(
            time=df[time_column].to_numpy(dtype=float),
            values=df[value_column].to_numpy(dtype=float),
            name=value_column,
            **kwargs,
        )

    @classmethod
    def from_parquet(
        cls,
        filepath: str | Path,
        **kwargs: Any,
    ) -> Curve:
        """Load a Curve from a Parquet file written by ``to_parquet``."""
        df = pd.read_parquet(filepath)
        return cls.from_dataframe(df, **kwargs)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_curve.py -v`
Expected: all pass, including `TestCurveRoundTrip`.

- [ ] **Step 5: Export the loaders (no API change needed — they're classmethods on Curve)**

Confirm `Curve` is already exported from `__init__.py` (it is). No edit needed.

- [ ] **Step 6: Commit**

```bash
git add src/dynaprocessing/models/curve.py tests/test_curve.py
git commit -m "feat: Curve.from_dataframe and from_parquet loaders"
```

---

## Task 7: Give `detect_oscillations` a real significance threshold

**Files:**
- Modify: `src/dynaprocessing/analysis/event_detection.py:160-205`
- Test: `tests/test_event_detection.py`

Currently any spectral content in band returns `oscillating: True`. We center the signal (remove DC) and require the dominant peak to stand clearly above the in-band median magnitude.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_event_detection.py`:

```python
def test_oscillation_detected_for_clean_sine():
    import numpy as np
    from dynaprocessing.models.curve import Curve
    from dynaprocessing.analysis.event_detection import detect_oscillations

    t = np.linspace(0, 10, 2000)
    sine = np.sin(2 * np.pi * 2.0 * t)  # 2 Hz
    curve = Curve(time=t, values=sine, name="osc")

    result = detect_oscillations(curve)
    assert result["oscillating"] is True
    assert abs(result["dominant_frequency"] - 2.0) < 0.1


def test_no_oscillation_for_flat_signal():
    import numpy as np
    from dynaprocessing.models.curve import Curve
    from dynaprocessing.analysis.event_detection import detect_oscillations

    t = np.linspace(0, 10, 2000)
    flat = np.full_like(t, 42.0)
    curve = Curve(time=t, values=flat, name="flat")

    result = detect_oscillations(curve)
    assert result["oscillating"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_event_detection.py::test_no_oscillation_for_flat_signal -v`
Expected: FAIL — flat signal currently reports `oscillating: True`.

- [ ] **Step 3: Update `detect_oscillations`**

In `src/dynaprocessing/analysis/event_detection.py`, change the signature to add `significance_factor: float = 5.0`, and replace the FFT body so it (a) removes the mean before the FFT and (b) requires the dominant magnitude to exceed `significance_factor × median(in-band magnitudes)`:

```python
def detect_oscillations(
    curve: Curve,
    min_frequency: float = 0.1,
    max_frequency: float = 10.0,
    significance_factor: float = 5.0,
) -> Dict:
    """Detect oscillations using FFT analysis.

    A signal is reported as oscillating only when a dominant in-band frequency
    stands clearly above the surrounding spectrum (dominant magnitude greater
    than ``significance_factor`` times the in-band median magnitude). This
    avoids labelling flat or monotonic signals as oscillating.
    """
    data = curve.values
    time = curve.time

    dt = float(np.mean(np.diff(time)))
    if dt <= 0:
        return {"oscillating": False}

    # Remove DC so a constant offset does not masquerade as signal energy.
    data_centered = data - np.mean(data)

    n = len(data_centered)
    fft_values = np.fft.fft(data_centered)
    fft_freq = np.fft.fftfreq(n, dt)

    freq_mask = (fft_freq >= min_frequency) & (fft_freq <= max_frequency)
    fft_freq_filtered = fft_freq[freq_mask]
    fft_mag_filtered = np.abs(fft_values[freq_mask])

    if len(fft_mag_filtered) == 0:
        return {"oscillating": False}

    dom_idx = int(np.argmax(fft_mag_filtered))
    dom_mag = float(fft_mag_filtered[dom_idx])
    median_mag = float(np.median(fft_mag_filtered))

    is_significant = median_mag > 0 and dom_mag > significance_factor * median_mag
    if not is_significant:
        return {"oscillating": False}

    dom_freq = abs(float(fft_freq_filtered[dom_idx]))
    return {
        "oscillating": True,
        "dominant_frequency": dom_freq,
        "period": 1.0 / dom_freq if dom_freq > 0 else float("inf"),
        "amplitude": float((data.max() - data.min()) / 2.0),
        "fft_magnitude": dom_mag,
    }
```

- [ ] **Step 4: Run the event-detection suite**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_event_detection.py -v`
Expected: all pass, including the two new tests.

- [ ] **Step 5: Commit**

```bash
git add src/dynaprocessing/analysis/event_detection.py tests/test_event_detection.py
git commit -m "fix: require spectral significance in detect_oscillations"
```

---

## Task 8: Harden sampling-frequency against duplicate/non-monotonic time

**Files:**
- Modify: `src/dynaprocessing/analysis/filters.py:17-38`
- Test: `tests/test_filters.py`

LS-DYNA restarts can repeat or reset timestamps. `get_sampling_frequency` uses the mean `dt` and only rejects a non-positive *mean*; a few duplicate stamps can skew it silently. Use the **median** positive `dt` (robust to a handful of zero/negative steps) and reject only when *no* positive step exists.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_filters.py` inside `class TestSamplingFrequency`:

```python
    def test_robust_to_duplicate_timestamp_block(self):
        # Uniform 1000 Hz, but a restart duplicates one stamp 50 times (dt=0).
        # The mean dt is skewed low by the extra zero-gaps (fs ~1050); the
        # median of the positive steps stays at the true 1000 Hz.
        # NOTE: a *single* duplicate does not skew the mean enough to fail, so
        # the test uses a block of 50 to genuinely discriminate median vs mean.
        t = list(np.linspace(0, 1, 1001))  # true dt = 0.001 → 1000 Hz
        for _ in range(50):
            t.insert(500, t[500])
        fs = get_sampling_frequency(np.array(t))
        assert pytest.approx(fs, rel=1e-2) == 1000.0

    def test_rejects_all_nonincreasing(self):
        with pytest.raises(ValueError, match="monotonically increasing"):
            get_sampling_frequency(np.array([5.0, 5.0, 5.0]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest "tests/test_filters.py::TestSamplingFrequency" -v`
Expected: `test_robust_to_duplicate_timestamp_block` FAILS (mean-based fs ≈ 1050, off by ~5%); the `test_rejects_all_nonincreasing` test already passes.

- [ ] **Step 3: Make `get_sampling_frequency` use the median positive step**

In `src/dynaprocessing/analysis/filters.py`, replace the body of `get_sampling_frequency` after the length check with:

```python
    diffs = np.diff(time_array)
    positive_steps = diffs[diffs > 0]
    if positive_steps.size == 0:
        raise ValueError("Time array must be monotonically increasing.")
    dt_median = float(np.median(positive_steps))
    return 1.0 / dt_median
```

- [ ] **Step 4: Run the filter suite**

Run: `/home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/test_filters.py -v`
Expected: all pass (existing uniform-timestep test still gives 1000 Hz; new robustness tests pass).

- [ ] **Step 5: Commit**

```bash
git add src/dynaprocessing/analysis/filters.py tests/test_filters.py
git commit -m "fix: robust sampling frequency via median positive timestep"
```

---

## Final verification

- [ ] **Run the entire suite and confirm green**

Run: `cd libs/dynaprocessing && /home/stepan/projects/PhD/AerisVault/.venv/bin/python -m pytest tests/ -q`
Expected: all tests pass, **no warnings**.

---

## Deferred to a separate follow-up plan (P3 structural)

These are real improvements from the review but form their own refactor cycle; they change return types or module boundaries and ripple into callers, so they are kept out of this plan to keep each task self-contained:

- **Dataclass return types for detectors** (`detect_deployment`/`inflation`/`steady_state` and `statistics`) instead of loosely-keyed dicts — improves safety and matches aerocfd's dataclass style, but changes the UI's access pattern; best done together with the FSI module pages.
- **Split `viz/plot_utils.py`** into `viz/web.py` (Plotly) and `viz/report.py` (matplotlib/PDF) for a clean web/report boundary.
- **Decouple metadata from directory names** — make `parse_*_directory` best-effort and let simulation models accept metadata injected from the DB rather than re-deriving it.
- **De-duplicate FFT logic** shared between `detect_oscillations` and `frequency_analysis`.

## Self-Review notes

- **Coverage vs review:** P1 → Tasks 1 (divide-by-zero), 2 (CFC), 3 (unify curves); P2 → Tasks 4 (extras), 5 (Path + version), 6 (round-trip); P3 hardening → Tasks 7 (oscillation), 8 (timestamps). Structural P3 explicitly deferred above.
- **Decision gate:** Task 2 changes CFC-filtered results — flagged at the top of the task for Stepan's sign-off before merge.
- **Type/name consistency:** new `list_curves` declared on `BaseSimulation` and implemented identically-named on both subclasses; `from_dataframe`/`from_parquet` use the same `value_column`/`time_column` parameter names across both methods and their tests.
- **Test data:** sample `.dat`/`.csv` contents in Task 3 match the parser expectations (header line starting with `time`/`Time`, `name@node-` headings, trailing comma).
```
