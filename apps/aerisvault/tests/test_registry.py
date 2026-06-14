"""Contract tests: every registered module must satisfy the descriptor invariants."""

from aerisvault.portal.registry import MODULES
from aerisvault.portal.descriptor import ModuleDescriptor


def test_registry_is_non_empty():
    assert len(MODULES) >= 1


def test_all_entries_are_descriptors():
    assert all(isinstance(m, ModuleDescriptor) for m in MODULES)


def test_keys_are_unique_and_lowercase():
    keys = [m.key for m in MODULES]
    assert len(keys) == len(set(keys)), "duplicate module keys"
    assert all(k == k.lower() and k for k in keys), "keys must be non-empty lowercase"


def test_titles_non_empty_and_pages_callable():
    for m in MODULES:
        assert m.title.strip(), f"{m.key} has empty title"
        assert callable(m.pages), f"{m.key} pages is not callable"


def test_fsi_module_registered():
    assert any(m.key == "fsi" for m in MODULES)
