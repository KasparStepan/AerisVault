"""Tests for LS-DYNA CSV and DAT file parsers."""

import numpy as np
import pytest
from pathlib import Path

from dynaprocessing.io.lsdyna_csv import parse_lsdyna_csv, parse_infinite_mass_dat
from dynaprocessing.models.curve import Curve


# ---------------------------------------------------------------------------
# Fixtures: create synthetic LS-DYNA output files
# ---------------------------------------------------------------------------

@pytest.fixture
def csv_file(tmp_path):
    """Create a synthetic LS-DYNA All_data.csv file."""
    content = (
        "Time,z_acceleration@13513-,Time,resultant_velocity@13513-,\n"
        "0.000,0.000,0.000,6.000,\n"
        "0.001,9.810,0.001,5.990,\n"
        "0.002,19.620,0.002,5.970,\n"
        "0.003,29.430,0.003,5.940,\n"
        "0.004,39.240,0.004,5.900,\n"
    )
    fp = tmp_path / "All_data.csv"
    fp.write_text(content)
    return fp


@pytest.fixture
def dat_file(tmp_path):
    """Create a synthetic LS-DYNA ICFD drag force .dat file."""
    content = (
        "LS-DYNA Output\n"
        "time Fpx Fpy Fpz Fvx Fvy Fvz\n"
        "0.000 100.0 10.0 -500.0 5.0 1.0 -25.0\n"
        "0.001 110.0 12.0 -520.0 5.5 1.2 -26.0\n"
        "0.002 105.0 11.0 -510.0 5.2 1.1 -25.5\n"
    )
    fp = tmp_path / "test_sim.dat"
    fp.write_text(content)
    return fp


# ---------------------------------------------------------------------------
# CSV Parser
# ---------------------------------------------------------------------------

class TestCSVParser:
    def test_parses_correct_number_of_curves(self, csv_file):
        data = parse_lsdyna_csv(csv_file)
        assert "13513" in data
        assert "z_acceleration" in data["13513"]
        assert "resultant_velocity" in data["13513"]

    def test_curve_values(self, csv_file):
        data = parse_lsdyna_csv(csv_file)
        accel = data["13513"]["z_acceleration"]
        assert isinstance(accel, Curve)
        assert len(accel) == 5
        assert accel.node_id == "13513"
        np.testing.assert_allclose(accel.values[0], 0.0)
        np.testing.assert_allclose(accel.values[1], 9.81, atol=0.01)

    def test_time_values(self, csv_file):
        data = parse_lsdyna_csv(csv_file)
        accel = data["13513"]["z_acceleration"]
        np.testing.assert_allclose(accel.time[0], 0.0)
        np.testing.assert_allclose(accel.time[-1], 0.004, atol=1e-6)

    def test_units_inferred(self, csv_file):
        data = parse_lsdyna_csv(csv_file)
        accel = data["13513"]["z_acceleration"]
        vel = data["13513"]["resultant_velocity"]
        assert accel.units == "m/s^2"
        assert vel.units == "m/s"

    def test_empty_file(self, tmp_path):
        fp = tmp_path / "empty.csv"
        fp.write_text("")
        data = parse_lsdyna_csv(fp)
        assert data == {}


# ---------------------------------------------------------------------------
# DAT Parser
# ---------------------------------------------------------------------------

class TestDATParser:
    def test_parses_all_columns(self, dat_file):
        curves = parse_infinite_mass_dat(dat_file)
        names = [c.name for c in curves]
        assert "Fpx" in names
        assert "Fpy" in names
        assert "Fpz" in names

    def test_z_inversion(self, dat_file):
        """Z-columns should be inverted (multiplied by -1) by default."""
        curves = parse_infinite_mass_dat(dat_file, invert_z=True)
        fpz = next(c for c in curves if c.name == "Fpz")
        # Original Fpz[0] = -500.0, inverted should be 500.0
        np.testing.assert_allclose(fpz.values[0], 500.0, atol=1e-6)

    def test_no_z_inversion(self, dat_file):
        """With invert_z=False, Z-columns should be left as-is."""
        curves = parse_infinite_mass_dat(dat_file, invert_z=False)
        fpz = next(c for c in curves if c.name == "Fpz")
        np.testing.assert_allclose(fpz.values[0], -500.0, atol=1e-6)

    def test_units_inferred(self, dat_file):
        curves = parse_infinite_mass_dat(dat_file)
        fpx = next(c for c in curves if c.name == "Fpx")
        assert fpx.units == "N"

    def test_curve_lengths(self, dat_file):
        curves = parse_infinite_mass_dat(dat_file)
        for c in curves:
            assert len(c) == 3

    def test_no_header_file(self, tmp_path):
        fp = tmp_path / "bad.dat"
        fp.write_text("no header here\njust numbers\n1 2 3\n")
        curves = parse_infinite_mass_dat(fp)
        assert curves == []
