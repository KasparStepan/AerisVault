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
