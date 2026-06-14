"""Portal landing page: one card per registered tool."""

import streamlit as st

from aerisvault.portal.registry import MODULES


def render():
    st.title("🚀 AerisVault")
    st.caption("A home for your engineering simulation tools.")
    st.divider()

    modules = sorted(MODULES, key=lambda m: m.order)
    columns = st.columns(3)
    for index, module in enumerate(modules):
        with columns[index % 3]:
            st.subheader(f"{module.icon} {module.title}")
            st.write(module.summary)
            if st.button(f"Open {module.title}", key=f"open_{module.key}", type="primary"):
                st.session_state["active_module"] = module.key
                st.rerun()
