"""aerocfd module — aircraft CFD polars (Fluent steady sweeps)."""
from aerisvault.portal.descriptor import ModuleDescriptor


def _pages():
    import streamlit as st
    from aerisvault.modules.aerocfd.pages import (
        aircraft, variants, operating_conditions, data_entry, analysis, comparison,
    )
    # Explicit url_path per page: the callables are all named render(), so
    # Streamlit would otherwise infer colliding pathnames (mirrors the FSI module).
    return [
        st.Page(aircraft.render,             title="Aircraft",             icon="✈️", url_path="aerocfd-aircraft"),
        st.Page(variants.render,             title="Variants",             icon="🛩️", url_path="aerocfd-variants"),
        st.Page(operating_conditions.render, title="Operating Conditions", icon="🌬️", url_path="aerocfd-operating-conditions"),
        st.Page(data_entry.render,           title="Data Entry",           icon="⌨️", url_path="aerocfd-data-entry"),
        st.Page(analysis.render,             title="Analysis",             icon="📈", url_path="aerocfd-analysis"),
        st.Page(comparison.render,           title="Comparison",           icon="⚖️", url_path="aerocfd-comparison"),
    ]


MODULE = ModuleDescriptor(
    key="aerocfd",
    title="Aircraft CFD",
    icon="✈️",
    summary="Build aircraft aerodynamic polars from raw Fluent loads.",
    pages=_pages,
    order=20,
)
