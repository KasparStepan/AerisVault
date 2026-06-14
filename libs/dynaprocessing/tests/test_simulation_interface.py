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
