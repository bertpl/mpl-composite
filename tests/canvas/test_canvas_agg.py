"""Artist-level tests on a real Agg-backend Axes (no display needed)."""

import pytest

from mpl_composite.canvas import Canvas, Region, artist_size
from mpl_composite.geometry import Range, XYZRange
from mpl_composite.style import TextStyle
from mpl_composite.transforms import Transform, XYZTransform


def _canvas_on(ax) -> Canvas:
    """Canvas whose plot coords equal the ax data coords (identity transforms on [0, 1])."""
    unit = Range(0.0, 1.0)
    region = Region(ax=ax, xyz=XYZRange(x=unit, y=unit, z=unit))
    identity = XYZTransform(
        x=Transform.linear(unit, unit),
        y=Transform.linear(unit, unit),
        z=Transform.linear(unit, unit),
    )
    return Canvas(region, identity)


def test_artist_size_measures_a_real_text(fig_ax) -> None:
    # --- arrange ----------------------
    fig, ax = fig_ax
    artist = ax.text(0.5, 0.5, "measure me", fontsize=12)

    # --- act --------------------------
    w, h = artist_size(fig, ax, artist)

    # --- assert -----------------------
    assert w > 0.0
    assert h > 0.0
    assert w > h  # a wide string is wider than tall


def test_text_size_monotonic_in_string_length(fig_ax) -> None:
    # --- arrange ----------------------
    _, ax = fig_ax
    canvas = _canvas_on(ax)

    # --- act --------------------------
    w_short, h_short = canvas.text_size("abc", TextStyle())
    w_long, h_long = canvas.text_size("abcabcabcabc", TextStyle())

    # --- assert -----------------------
    assert 0.0 < w_short < w_long
    assert h_short > 0.0
    assert h_long == h_short  # same font size: same height
    assert not ax.texts  # temporary artists were removed


def test_text_size_scales_with_font_size(fig_ax) -> None:
    # --- arrange ----------------------
    _, ax = fig_ax
    canvas = _canvas_on(ax)

    # --- act --------------------------
    w_small, _ = canvas.text_size("abc", TextStyle(size=8.0))
    w_large, _ = canvas.text_size("abc", TextStyle(size=16.0))

    # --- assert -----------------------
    assert w_large > 1.5 * w_small


def test_rotated_text_aspect_is_positive_and_finite(fig_ax) -> None:
    # --- arrange ----------------------
    _, ax = fig_ax
    canvas = _canvas_on(ax)

    # --- act --------------------------
    aspect = canvas.rotated_text_aspect(45.0)

    # --- assert -----------------------
    assert 0.0 < aspect < 100.0


def test_rectangle_lands_on_the_axes(fig_ax) -> None:
    # --- arrange ----------------------
    _, ax = fig_ax
    canvas = _canvas_on(ax)

    # --- act --------------------------
    canvas.rectangle(0.1, 0.4, 0.2, 0.8, fill_color=(0.5, 0.5, 0.5))

    # --- assert -----------------------
    (rect,) = ax.patches
    assert rect.get_xy() == pytest.approx((0.1, 0.2))
    assert rect.get_width() == pytest.approx(0.3)
    assert rect.get_height() == pytest.approx(0.6)
