"""Tests for the module contract (ModuleDescriptor)."""

import pytest
from aerisvault.portal.descriptor import ModuleDescriptor


def test_descriptor_is_frozen():
    """A descriptor must be immutable so a module's identity can't be mutated at runtime."""
    module = ModuleDescriptor(
        key="demo",
        title="Demo",
        icon="🧪",
        summary="A demo tool.",
        pages=lambda: [],
    )
    with pytest.raises(Exception):
        module.key = "changed"


def test_pages_is_callable_returning_list():
    """pages must be a zero-arg callable that returns a list (built lazily, not at import time)."""
    module = ModuleDescriptor(
        key="demo",
        title="Demo",
        icon="🧪",
        summary="A demo tool.",
        pages=lambda: ["page_a", "page_b"],
    )
    assert callable(module.pages)
    assert module.pages() == ["page_a", "page_b"]


def test_default_order_is_100():
    module = ModuleDescriptor(
        key="demo", title="Demo", icon="🧪", summary="x", pages=lambda: []
    )
    assert module.order == 100
