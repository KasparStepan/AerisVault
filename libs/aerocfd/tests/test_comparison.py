import numpy as np
import pytest

from aerocfd.analysis.comparison import ComparisonResult, compare_polars
from aerocfd.models.polar import Polar


def test_compare_polars_common_alpha_and_delta():
    a = Polar([0.0, 5.0, 10.0], [0.10, 0.20, 0.30], name="CL")
    b = Polar([0.0, 5.0, 10.0], [0.15, 0.25, 0.35], name="CL")
    result = compare_polars(a, b)
    assert isinstance(result, ComparisonResult)
    assert result.name == "CL"
    assert np.allclose(result.alpha_deg, [0.0, 5.0, 10.0])
    assert np.allclose(result.values_a, [0.10, 0.20, 0.30])
    assert np.allclose(result.values_b, [0.15, 0.25, 0.35])
    assert np.allclose(result.delta, [0.05, 0.05, 0.05])  # B − A


def test_compare_polars_uses_alpha_intersection():
    a = Polar([0.0, 5.0, 10.0], [0.1, 0.2, 0.3], name="CL")
    b = Polar([5.0, 10.0, 15.0], [0.2, 0.3, 0.4], name="CL")
    result = compare_polars(a, b)
    assert np.allclose(result.alpha_deg, [5.0, 10.0])


def test_compare_polars_custom_grid_interpolates():
    a = Polar([0.0, 10.0], [0.0, 1.0], name="CL")
    b = Polar([0.0, 10.0], [0.0, 2.0], name="CL")
    result = compare_polars(a, b, alpha_grid=[5.0])
    assert result.values_a[0] == pytest.approx(0.5)
    assert result.values_b[0] == pytest.approx(1.0)
    assert result.delta[0] == pytest.approx(0.5)
