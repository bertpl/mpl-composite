import importlib

import pytest

# The declared public surface: the root package plus every re-exporting
# subpackage. Run against an installed wheel (the package-check pipeline),
# this proves every public module ships and every `__all__` name resolves.
PUBLIC_MODULES = [
    "mpl_composite",
    "mpl_composite.axis",
    "mpl_composite.canvas",
    "mpl_composite.elements",
    "mpl_composite.figure",
    "mpl_composite.geometry",
    "mpl_composite.plot",
    "mpl_composite.style",
    "mpl_composite.table",
    "mpl_composite.transforms",
]


@pytest.mark.parametrize("module_name", PUBLIC_MODULES)
def test_all_exports_resolve(module_name: str) -> None:
    # --- arrange ----------------------
    module = importlib.import_module(module_name)

    # --- act / assert -----------------
    assert module.__all__, f"{module_name}.__all__ is empty"
    for name in module.__all__:
        getattr(module, name)  # raises AttributeError on a stale __all__ entry
