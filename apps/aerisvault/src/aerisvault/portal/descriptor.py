"""The module contract: how a tool advertises itself to the portal shell."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModuleDescriptor:
    """How a tool advertises itself to the portal shell.

    A module is fully described by this object. The shell never reaches into a
    module's internals — it only reads this descriptor to build the landing page
    and the navigation menu.
    """

    key: str                       # stable id, e.g. "fsi"; also the data namespace (data/<key>/)
    title: str                     # shown on the card and menu, e.g. "Parachute FSI"
    icon: str                      # emoji or Streamlit material icon, e.g. "🪂"
    summary: str                   # one line for the portal card
    pages: Callable[[], list[Any]] # returns this module's st.Page list WHEN CALLED
    order: int = 100               # sort order on the portal home
