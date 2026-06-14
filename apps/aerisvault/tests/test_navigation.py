"""Tests for the two-level navigation builder."""

from aerisvault.portal.descriptor import ModuleDescriptor
from aerisvault.shared.navigation import pages_for_active_module


def _module(key, marker):
    return ModuleDescriptor(
        key=key, title=key.upper(), icon="🧪", summary="x",
        pages=lambda: [f"{marker}-page"],
    )


def test_no_active_module_returns_none():
    """When no module is active, the shell shows the portal home (None = home)."""
    modules = [_module("fsi", "fsi"), _module("aerocfd", "cfd")]
    assert pages_for_active_module(modules, active_key=None) is None


def test_active_module_returns_only_its_pages():
    modules = [_module("fsi", "fsi"), _module("aerocfd", "cfd")]
    assert pages_for_active_module(modules, active_key="aerocfd") == ["cfd-page"]


def test_unknown_active_key_returns_none():
    """A stale/unknown active key falls back to the portal home rather than crashing."""
    modules = [_module("fsi", "fsi")]
    assert pages_for_active_module(modules, active_key="ghost") is None
