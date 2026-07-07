from unittest.mock import Mock

import pytest

from mpl_composite.canvas import Region
from mpl_composite.elements import Spacer, Text
from mpl_composite.geometry import XYZ, HAlign, Range, VAlign, XYZRange


def _region(ax) -> Region:
    return Region(ax=ax, xyz=XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 1.0)))


# ==================================================================================================
#  Spacer
# ==================================================================================================
def test_spacer_measures_declared_box_with_no_z() -> None:
    # --- act / assert -----------------
    assert Spacer(2.0, 3.0).measure() == XYZ(2.0, 3.0, 0.0)


def test_spacer_draws_nothing() -> None:
    # --- arrange ----------------------
    ax = Mock()
    spacer = Spacer(1.0, 1.0)
    layout = spacer.place(_region(ax))

    # --- act --------------------------
    spacer.draw(layout)

    # --- assert -----------------------
    ax.plot.assert_not_called()
    ax.text.assert_not_called()


def test_spacer_rejects_negative_sizes() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match=">= 0"):
        Spacer(-1.0, 1.0)


# ==================================================================================================
#  Text
# ==================================================================================================
@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"x_size": 0.0, "y_size": 1.0}, "> 0"),
        ({"x_size": 1.0, "y_size": 1.0, "fill_fraction": 0.0}, r"\(0, 1\]"),
        ({"x_size": 1.0, "y_size": 1.0, "fill_fraction": 1.5}, r"\(0, 1\]"),
    ],
)
def test_text_rejects_invalid_construction(kwargs: dict, match: str) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match=match):
        Text(text="hi", **kwargs)


def test_text_measures_declared_box() -> None:
    # --- act / assert -----------------
    assert Text(3.0, 1.0, "hello").measure() == XYZ(3.0, 1.0, 0.0)


def test_text_draws_one_scaled_artist(fig_ax) -> None:
    # --- arrange ----------------------
    _, ax = fig_ax
    text = Text(0.8, 0.2, "hello world")
    layout = text.place(_region(ax))

    # --- act --------------------------
    text.draw(layout)

    # --- assert -----------------------
    (artist,) = ax.texts
    assert artist.get_text() == "hello world"
    assert artist.get_fontsize() > 0.0


def test_text_alignment_moves_the_anchor(fig_ax) -> None:
    # --- arrange ----------------------
    _, ax = fig_ax
    left = Text(0.8, 0.2, "x", h_align=HAlign.LEFT, v_align=VAlign.BOTTOM)
    right = Text(0.8, 0.2, "x", h_align=HAlign.RIGHT, v_align=VAlign.TOP)

    # --- act --------------------------
    left.draw(left.place(_region(ax)))
    right.draw(right.place(_region(ax)))

    # --- assert -----------------------
    a_left, a_right = ax.texts
    assert a_left.get_position()[0] < a_right.get_position()[0]
    assert a_left.get_position()[1] < a_right.get_position()[1]
    assert a_left.get_ha() == "left"
    assert a_right.get_ha() == "right"


def test_empty_text_draws_nothing(fig_ax) -> None:
    # --- arrange ----------------------
    _, ax = fig_ax
    text = Text(1.0, 1.0, "")
    layout = text.place(_region(ax))

    # --- act --------------------------
    text.draw(layout)

    # --- assert -----------------------
    assert not ax.texts
