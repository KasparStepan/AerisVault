"""Build a tidy comparison table (and CSV) from ComparisonResults.

Lives app-side so the pure library stays pandas-free. One row per α; for each
coefficient three columns: value for A, value for B, and Δ (= B − A).
"""
from __future__ import annotations

import pandas as pd

from aerocfd.analysis.comparison import ComparisonResult


def comparison_dataframe(
    label_a: str, label_b: str, results: dict[str, ComparisonResult]
) -> pd.DataFrame:
    """Assemble a comparison table. `results` maps coefficient name → ComparisonResult;
    all results must share the same α grid (compare on a common grid)."""
    coefficients = list(results.items())
    if not coefficients:
        return pd.DataFrame()
    alpha = coefficients[0][1].alpha_deg
    columns = {"α [deg]": alpha}
    for name, result in coefficients:
        columns[f"{name} · {label_a}"] = result.values_a
        columns[f"{name} · {label_b}"] = result.values_b
        columns[f"Δ{name}"] = result.delta
    return pd.DataFrame(columns)


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    """UTF-8 CSV bytes for a Streamlit download button."""
    return dataframe.to_csv(index=False).encode("utf-8")
