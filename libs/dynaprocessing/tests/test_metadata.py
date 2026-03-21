"""Tests for metadata parsing from directory names."""

import pytest

from dynaprocessing.io.metadata import (
    FiniteMassMetadata,
    InfiniteMassMetadata,
    parse_finite_mass_directory,
    parse_infinite_mass_directory,
)


class TestFiniteMassMetadata:
    def test_valid_directory(self):
        meta = parse_finite_mass_directory("/some/path/cross_2m_6kg_6ms")
        assert isinstance(meta, FiniteMassMetadata)
        assert meta.parachute_type == "cross"
        assert meta.size == "2m"
        assert meta.mass == "6kg"
        assert meta.initial_velocity == "6ms"

    def test_label(self):
        meta = parse_finite_mass_directory("/path/cross_2m_6kg_6ms")
        assert meta.label == "cross 2m | 6kg (6ms)"

    def test_rejects_too_few_parts(self):
        with pytest.raises(ValueError, match="4 underscore-separated"):
            parse_finite_mass_directory("/path/cross_2m_6kg")

    def test_rejects_too_many_parts(self):
        with pytest.raises(ValueError, match="4 underscore-separated"):
            parse_finite_mass_directory("/path/cross_2m_6kg_6ms_extra")


class TestInfiniteMassMetadata:
    def test_valid_directory(self):
        meta = parse_infinite_mass_directory("/path/scrab_2m_40ms_folded")
        assert isinstance(meta, InfiniteMassMetadata)
        assert meta.parachute_type == "scrab"
        assert meta.size == "2m"
        assert meta.flow_velocity == "40ms"
        assert meta.simulation_type == "folded"
        assert meta.additional_info == ""

    def test_with_extra_info(self):
        meta = parse_infinite_mass_directory("/path/scrab_2m_40ms_folded_v2_rev")
        assert meta.simulation_type == "folded"
        assert meta.additional_info == "v2_rev"

    def test_label(self):
        meta = parse_infinite_mass_directory("/path/scrab_2m_40ms_inflated")
        assert meta.label == "scrab 2m | 40ms (inflated)"

    def test_rejects_too_few_parts(self):
        with pytest.raises(ValueError, match="at least 4"):
            parse_infinite_mass_directory("/path/scrab_2m_40ms")
