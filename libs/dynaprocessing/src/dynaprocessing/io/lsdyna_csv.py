"""Parsers for LS-DYNA output files (.csv and .dat).

These functions handle the quirks of LS-DYNA's text export formats:
- trailing commas creating phantom columns
- paired Time/Value column layout in CSV exports
- Fortran-style number formatting in .dat files
- header detection in files with preamble lines
"""

import logging
import re
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from dynaprocessing.models.curve import Curve

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Unit mapping: infer units from curve names at parse time
# ---------------------------------------------------------------------------
_UNIT_MAP = {
    "acceleration": "m/s^2",
    "velocity": "m/s",
    "displacement": "m",
    "force": "N",
    "moment": "N*m",
}


def _infer_units(curve_name: str) -> str | None:
    """Infer physical units from a curve name using keyword matching."""
    lower = curve_name.lower()
    for keyword, unit in _UNIT_MAP.items():
        if keyword in lower:
            return unit
    return None


# ---------------------------------------------------------------------------
# CSV parser (Finite Mass — All_data.csv, Accel.csv)
# ---------------------------------------------------------------------------

def parse_lsdyna_csv(
    filepath: str | Path,
) -> Dict[str, Dict[str, Curve]]:
    """Parse an LS-DYNA CSV export file into Curve objects.

    LS-DYNA CSV files typically have:
    - A trailing comma on every line (creating an empty final column)
    - Alternating Time / Data column pairs
    - Data headers in the format ``variable_name@node_id-``

    Args:
        filepath: Path to the CSV file.

    Returns:
        Nested dict ``{node_id: {curve_name: Curve}}``.
    """
    filepath = Path(filepath)
    with open(filepath, "r") as fh:
        lines = fh.readlines()

    if not lines:
        logger.warning("File %s is empty.", filepath)
        return {}

    # Locate the header line (first line starting with 'Time')
    header_idx = 0
    for idx, line in enumerate(lines):
        if line.strip().lower().startswith("time"):
            header_idx = idx
            break

    headers = lines[header_idx].strip().split(",")

    # Strip trailing empty header from LS-DYNA's trailing comma
    if headers and headers[-1].strip() == "":
        headers = headers[:-1]

    # Load numeric data, skipping everything up to and including the header
    df = pd.read_csv(filepath, skiprows=header_idx + 1, header=None)

    # Align column count
    if df.shape[1] > len(headers):
        df = df.iloc[:, : len(headers)]

    # Parse column pairs: (Time, DataColumn), (Time, DataColumn), ...
    curves_data: Dict[str, Dict[str, Curve]] = {}

    for i in range(0, len(headers), 2):
        if i + 1 >= len(headers):
            break

        data_heading = headers[i + 1].strip()

        time_col = df.iloc[:, i].dropna().to_numpy(dtype=float)
        data_col = df.iloc[:, i + 1].dropna().to_numpy(dtype=float)

        # Ensure equal lengths
        min_len = min(len(time_col), len(data_col))
        time_col = time_col[:min_len]
        data_col = data_col[:min_len]

        # Parse heading format: 'z_acceleration@13513-'
        match = re.match(r"(.*)@(\d+)-?", data_heading)
        if match:
            curve_name = match.group(1)
            node_id = match.group(2)
        else:
            curve_name = data_heading
            node_id = "global"

        curves_data.setdefault(node_id, {})
        curves_data[node_id][curve_name] = Curve(
            time=time_col,
            values=data_col,
            name=curve_name,
            node_id=node_id,
            units=_infer_units(curve_name),
        )

    logger.info(
        "Parsed %d curves from %s",
        sum(len(v) for v in curves_data.values()),
        filepath.name,
    )
    return curves_data


# ---------------------------------------------------------------------------
# DAT parser (Infinite Mass — ICFD drag forces)
# ---------------------------------------------------------------------------

def parse_infinite_mass_dat(
    filepath: str | Path,
    invert_z: bool = True,
) -> List[Curve]:
    """Parse an LS-DYNA ICFD drag-force ``.dat`` file.

    These files contain space-separated columns with a header line
    starting with ``time``. Columns typically include: Fpx, Fpy, Fpz,
    Fvx, Fvy, Fvz, Mpx, Mpy, Mpz, Mvx, Mvy, Mvz.

    Args:
        filepath: Path to the .dat file.
        invert_z: If True, multiply Z-direction columns by -1
            to follow the standard engineering sign convention
            (positive = upward drag). Default True.

    Returns:
        List of Curve objects, one per data column.
    """
    filepath = Path(filepath)

    # Locate the header line
    header_line = ""
    skip_lines = 0
    with open(filepath, "r") as fh:
        for idx, line in enumerate(fh):
            stripped = line.strip()
            if stripped.lower().startswith("time"):
                header_line = stripped
                skip_lines = idx + 1

    if not header_line:
        logger.warning("No header found in %s", filepath)
        return []

    # Normalize delimiters (some files use commas, some spaces)
    header_line = header_line.replace(",", " ")
    headers = [h.strip() for h in header_line.split() if h.strip()]

    df = pd.read_csv(
        filepath,
        skiprows=skip_lines,
        sep=r"\s+",
        header=None,
        names=headers,
        on_bad_lines="skip",
    )

    # Extract time column
    time_col_name = next(
        (c for c in df.columns if c.lower() == "time"), df.columns[0]
    )
    time_data = df[time_col_name].to_numpy(dtype=float)

    curves: List[Curve] = []
    for col in df.columns:
        if col.lower() == "time":
            continue

        vals = df[col].to_numpy(dtype=float)

        # Optionally invert Z-direction for standard sign convention
        if invert_z and col.lower().endswith("z"):
            vals = vals * -1.0
            logger.debug(
                "Inverted Z-direction column '%s' in %s", col, filepath.name
            )

        # Infer units from column name
        units = None
        lower_col = col.lower()
        if lower_col.startswith("f"):
            units = "N"
        elif lower_col.startswith("m"):
            units = "N*m"

        curves.append(
            Curve(
                time=time_data,
                values=vals,
                name=col,
                node_id=None,
                units=units,
            )
        )

    logger.info("Parsed %d curves from %s", len(curves), filepath.name)
    return curves
