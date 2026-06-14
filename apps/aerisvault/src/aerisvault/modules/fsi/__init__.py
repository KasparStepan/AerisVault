"""FSI module: post-processing of LS-DYNA parachute force histories."""

from aerisvault.portal.descriptor import ModuleDescriptor


def _pages():
    import streamlit as st
    from aerisvault.modules.fsi.pages import (
        database,
        single_analysis,
        comparison,
        settings,
    )
    # Every page's callable is named render(), so Streamlit would infer the same
    # URL pathname for all four and reject them as duplicates. Give each an
    # explicit, unique url_path. Prefix with the module key to stay unique across
    # modules once more tools are registered.
    return [
        st.Page(database.render,        title="Database",        icon="🗄️", url_path="fsi-database"),
        st.Page(single_analysis.render, title="Single Analysis", icon="📈", url_path="fsi-single-analysis"),
        st.Page(comparison.render,      title="Comparison",      icon="⚖️", url_path="fsi-comparison"),
        st.Page(settings.render,        title="Settings",        icon="⚙️", url_path="fsi-settings"),
    ]


MODULE = ModuleDescriptor(
    key="fsi",
    title="Parachute FSI",
    icon="🪂",
    summary="Post-process LS-DYNA parachute force histories.",
    pages=_pages,
    order=10,
)
