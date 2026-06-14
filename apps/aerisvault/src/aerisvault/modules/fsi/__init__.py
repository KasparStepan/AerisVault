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
    return [
        st.Page(database.render,        title="Database",        icon="🗄️"),
        st.Page(single_analysis.render, title="Single Analysis", icon="📈"),
        st.Page(comparison.render,      title="Comparison",      icon="⚖️"),
        st.Page(settings.render,        title="Settings",        icon="⚙️"),
    ]


MODULE = ModuleDescriptor(
    key="fsi",
    title="Parachute FSI",
    icon="🪂",
    summary="Post-process LS-DYNA parachute force histories.",
    pages=_pages,
    order=10,
)
