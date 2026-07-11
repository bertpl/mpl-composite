import importlib
import pkgutil

import pytest

import mpl_composite

# The public surface, discovered from the installed package: the root plus
# every non-underscore subpackage. Run against an installed wheel (the
# package-check pipeline), this proves every public module ships with a
# non-empty `__all__` whose names all resolve.
PUBLIC_MODULES = ["mpl_composite"] + [
    f"mpl_composite.{module.name}"
    for module in pkgutil.iter_modules(mpl_composite.__path__)
    if not module.name.startswith("_")
]


@pytest.mark.parametrize("module_name", PUBLIC_MODULES)
def test_all_exports_resolve(module_name: str) -> None:
    # --- arrange ----------------------
    module = importlib.import_module(module_name)

    # --- act / assert -----------------
    assert module.__all__, f"{module_name}.__all__ is empty"
    for name in module.__all__:
        getattr(module, name)  # raises AttributeError on a stale __all__ entry
