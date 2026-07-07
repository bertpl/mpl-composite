import pytest

from mpl_composite.style import FontWeight, TextStyle


def test_defaults() -> None:
    # --- act --------------------------
    ts = TextStyle()

    # --- assert -----------------------
    assert ts.size == 10.0
    assert ts.weight is FontWeight.NORMAL
    assert ts.rotation_deg == 0.0


def test_modify() -> None:
    # --- arrange ----------------------
    ts = TextStyle(size=12.0)

    # --- act --------------------------
    modified = ts.modify(weight=FontWeight.BOLD, rotation_deg=45.0)

    # --- assert -----------------------
    assert modified == TextStyle(size=12.0, weight=FontWeight.BOLD, rotation_deg=45.0)
    assert ts.weight is FontWeight.NORMAL  # original untouched


def test_font_weight_values_are_matplotlib_strings() -> None:
    # --- act / assert -----------------
    assert FontWeight.SEMI_BOLD == "semibold"
    assert FontWeight.BOLD == "bold"


def test_modify_rejects_unknown_field() -> None:
    # --- act / assert -----------------
    with pytest.raises(TypeError):
        TextStyle().modify(nope=1.0)
