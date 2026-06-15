"""Reusable aerocfd widgets — selection pickers shared across pages.

The pickers persist the current selection in namespaced session-state keys
(aerocfd.current_aircraft_id / aerocfd.current_operating_condition_id) so a
choice made on one page carries to the next.
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

from aerisvault.modules.aerocfd.core.models import (
    AircraftORM, AircraftVariantORM, OperatingConditionORM,
)


def aircraft_picker(label: str = "Aircraft") -> Optional[AircraftORM]:
    """Dropdown of all aircraft. Returns the selected AircraftORM, or None if none exist."""
    db = st.session_state["aerocfd.db"]
    aircraft = db.list_aircraft()
    if not aircraft:
        st.info("No aircraft yet. Create one on the Aircraft page.")
        return None

    current_id = st.session_state.get("aerocfd.current_aircraft_id")
    default_index = next((i for i, a in enumerate(aircraft) if a.id == current_id), 0)
    labels = [f"{a.name}  (id {a.id})" for a in aircraft]
    chosen = st.selectbox(label, labels, index=default_index)
    selected = aircraft[labels.index(chosen)]
    st.session_state["aerocfd.current_aircraft_id"] = selected.id
    return selected


def variant_picker(aircraft_id: int, label: str = "Variant") -> Optional[AircraftVariantORM]:
    """Dropdown of variants for one aircraft. Returns the selected variant, or None."""
    db = st.session_state["aerocfd.db"]
    variants = db.list_variants(aircraft_id)
    if not variants:
        st.info("No variants for this aircraft yet. Add one on the Variants page.")
        return None

    current_id = st.session_state.get("aerocfd.current_variant_id")
    default_index = next((i for i, v in enumerate(variants) if v.id == current_id), 0)
    labels = [f"{v.name}  (id {v.id})" for v in variants]
    chosen = st.selectbox(label, labels, index=default_index)
    selected = variants[labels.index(chosen)]
    st.session_state["aerocfd.current_variant_id"] = selected.id
    return selected


def operating_condition_picker(
    variant_id: int, label: str = "Operating condition"
) -> Optional[OperatingConditionORM]:
    """Dropdown of operating conditions for one variant. Returns the selected OC, or None."""
    db = st.session_state["aerocfd.db"]
    operating_conditions = db.list_operating_conditions(variant_id)
    if not operating_conditions:
        st.info("No operating conditions for this variant yet. Add one on the Operating Conditions page.")
        return None

    current_id = st.session_state.get("aerocfd.current_operating_condition_id")
    default_index = next(
        (i for i, oc in enumerate(operating_conditions) if oc.id == current_id), 0
    )
    labels = [f"{oc.name}  (id {oc.id})" for oc in operating_conditions]
    chosen = st.selectbox(label, labels, index=default_index)
    selected = operating_conditions[labels.index(chosen)]
    st.session_state["aerocfd.current_operating_condition_id"] = selected.id
    return selected
