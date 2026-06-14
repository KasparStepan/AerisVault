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


class TestAspectRatio:
    """Coefficient-vs-α curves (CL, CD, Cm) are tall 1:2; L/D and the drag polar
    are square 1:1."""

    def test_coefficient_curves_are_1to2(self, cl_polar, cd_polar):
        cm = Polar(cl_polar.alpha_deg, np.array([0.05, 0.0, -0.05, -0.1]), name="Cm", units="-")
        for fig in (cl_alpha_figure(cl_polar), cd_alpha_figure(cd_polar), cm_alpha_figure(cm)):
            assert fig.layout.height == pytest.approx(2 * fig.layout.width)

    def test_efficiency_is_square(self, cl_polar):
        ld = Polar(cl_polar.alpha_deg, np.array([0.0, 5.0, 12.0, 10.0]), name="L/D", units="-")
        fig = lift_to_drag_alpha_figure(ld)
        assert fig.layout.height == pytest.approx(fig.layout.width)

    def test_drag_polar_is_square(self, cl_polar, cd_polar):
        fig = drag_polar_figure(cl_polar, cd_polar)
        assert fig.layout.height == pytest.approx(fig.layout.width)
