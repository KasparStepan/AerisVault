"""AerisVault portal shell.

One Streamlit app hosting many tools as self-contained modules. The portal home
lists the tools; selecting one shows only that module's pages (two-level
navigation). Run with:

    streamlit run apps/aerisvault/src/aerisvault/app.py
"""

import streamlit as st

from aerisvault.portal.home import render as render_home
from aerisvault.portal.registry import MODULES
from aerisvault.shared.navigation import pages_for_active_module

st.set_page_config(
    page_title="AerisVault",
    page_icon="🪂",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _go_home():
    st.session_state["active_module"] = None


active_key = st.session_state.get("active_module")
module_pages = pages_for_active_module(MODULES, active_key)

if module_pages is None:
    # No module selected (or stale key) → portal home.
    home_page = st.Page(render_home, title="All tools", icon="🏠")
    st.navigation([home_page]).run()
else:
    # Inside a module → only its pages, plus a way back to the portal.
    st.sidebar.button("← All tools", on_click=_go_home, use_container_width=True)
    active_module = next(m for m in MODULES if m.key == active_key)
    st.sidebar.title(f"{active_module.icon} {active_module.title}")
    st.navigation(module_pages).run()
