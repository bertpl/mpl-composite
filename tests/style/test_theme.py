from mpl_composite.style import DEFAULT_THEME, LineStyle, Theme


def test_default_theme_is_a_populated_theme() -> None:
    # --- act / assert -----------------
    assert isinstance(DEFAULT_THEME, Theme)
    assert Theme() == DEFAULT_THEME
    assert DEFAULT_THEME.border_major.width > DEFAULT_THEME.border_minor.width


def test_modify_specializes_without_touching_the_original() -> None:
    # --- arrange ----------------------
    thick_border = LineStyle(width=3.0)

    # --- act --------------------------
    specialized = DEFAULT_THEME.modify(border_major=thick_border)

    # --- assert -----------------------
    assert specialized.border_major == thick_border
    assert specialized.text == DEFAULT_THEME.text  # untouched fields carried over
    assert DEFAULT_THEME.border_major != thick_border  # original untouched
