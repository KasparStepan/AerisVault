"""Two-level navigation: portal home, then one module at a time.

The pure decision (which module's pages to show) lives in
pages_for_active_module so it can be unit-tested without Streamlit. The
Streamlit wiring that turns that decision into st.navigation lives in app.py.
"""

from typing import Any, Optional

from aerisvault.portal.descriptor import ModuleDescriptor


def pages_for_active_module(
    modules: list[ModuleDescriptor],
    active_key: Optional[str],
) -> Optional[list[Any]]:
    """Return the active module's pages, or None to show the portal home.

    None is returned when no module is active OR when active_key does not match
    any registered module (a stale key falls back to the home page).
    """
    if active_key is None:
        return None
    for module in modules:
        if module.key == active_key:
            return module.pages()
    return None
