"""Tests for the comparison table and its CSV export."""

import io

import numpy as np
import pandas as pd

from aerocfd.analysis.comparison import compare_polars
from aerocfd.models.polar import Polar

from aerisvault.modules.aerocfd.core.csv_export import (
    comparison_dataframe, dataframe_to_csv_bytes,
)


def _results():
    cl_a = Polar([0.0, 5.0, 10.0], [0.10, 0.20, 0.30], name="CL")
    cl_b = Polar([0.0, 5.0, 10.0], [0.15, 0.25, 0.35], name="CL")
    cd_a = Polar([0.0, 5.0, 10.0], [0.01, 0.02, 0.05], name="CD")
    cd_b = Polar([0.0, 5.0, 10.0], [0.02, 0.03, 0.06], name="CD")
    return {"CL": compare_polars(cl_a, cl_b), "CD": compare_polars(cd_a, cd_b)}


def test_comparison_dataframe_columns_and_values():
    df = comparison_dataframe("A", "B", _results())
    assert list(df.columns) == [
        "α [deg]", "CL · A", "CL · B", "ΔCL", "CD · A", "CD · B", "ΔCD",
    ]
    assert np.allclose(df["α [deg]"], [0.0, 5.0, 10.0])
    assert np.allclose(df["ΔCL"], [0.05, 0.05, 0.05])


def test_csv_round_trips_through_pandas():
    df = comparison_dataframe("A", "B", _results())
    csv_bytes = dataframe_to_csv_bytes(df)
    reloaded = pd.read_csv(io.BytesIO(csv_bytes))
    assert np.allclose(reloaded["ΔCD"], df["ΔCD"])
    assert np.allclose(reloaded["α [deg]"], [0.0, 5.0, 10.0])
