"""aerocfd module — aircraft CFD polars (Fluent steady sweeps)."""
from aerisvault.portal.descriptor import ModuleDescriptor


def _pages():
    import streamlit as st
    from aerisvault.modules.aerocfd.pages import polar
    # Explicit url_path: the page callable is render(), so Streamlit would infer
    # a generic pathname — name it to stay unique (mirrors the FSI module).
    return [st.Page(polar.render, title="Polar", icon="✈️", url_path="aerocfd-polar")]


MODULE = ModuleDescriptor(
    key="aerocfd",
    title="Aircraft CFD",
    icon="✈️",
    summary="Build aircraft aerodynamic polars from raw Fluent loads.",
    pages=_pages,
    order=20,
)
