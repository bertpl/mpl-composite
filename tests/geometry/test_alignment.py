import pytest

from mpl_composite.geometry import HAlign, Margin, Range, VAlign


# ==================================================================================================
#  HAlign
# ==================================================================================================
@pytest.mark.parametrize(
    "align, expected",
    [
        (HAlign.LEFT, Range(0.0, 4.0)),
        (HAlign.RIGHT, Range(6.0, 10.0)),
        (HAlign.CENTER, Range(3.0, 7.0)),
        (HAlign.FILL, Range(0.0, 10.0)),
    ],
)
def test_halign_fit(align: HAlign, expected: Range) -> None:
    # --- act / assert -----------------
    assert align.fit(Range(0.0, 10.0), 4.0) == expected


# ==================================================================================================
#  VAlign — both orientations
# ==================================================================================================
@pytest.mark.parametrize(
    "align, expected",
    [
        (VAlign.TOP, Range(6.0, 10.0)),  # y-up: top is the max side
        (VAlign.BOTTOM, Range(0.0, 4.0)),
        (VAlign.CENTER, Range(3.0, 7.0)),
        (VAlign.FILL, Range(0.0, 10.0)),
    ],
)
def test_valign_fit_y_up(align: VAlign, expected: Range) -> None:
    # --- act / assert -----------------
    assert align.fit(Range(0.0, 10.0), 4.0) == expected


@pytest.mark.parametrize(
    "align, expected",
    [
        (VAlign.TOP, Range(0.0, 4.0)),  # top-down: top is the min side
        (VAlign.BOTTOM, Range(6.0, 10.0)),
        (VAlign.CENTER, Range(3.0, 7.0)),
        (VAlign.FILL, Range(0.0, 10.0)),
    ],
)
def test_valign_fit_top_down(align: VAlign, expected: Range) -> None:
    # --- act / assert -----------------
    assert align.fit(Range(0.0, 10.0), 4.0, top_at_max=False) == expected


# ==================================================================================================
#  Margin
# ==================================================================================================
def test_margin_defaults_to_zero() -> None:
    # --- act --------------------------
    margin = Margin()

    # --- assert -----------------------
    assert (margin.left, margin.right, margin.top, margin.bottom) == (0.0, 0.0, 0.0, 0.0)
    assert margin.width == 0.0
    assert margin.height == 0.0


def test_margin_uniform_and_totals() -> None:
    # --- act --------------------------
    margin = Margin.uniform(0.5)

    # --- assert -----------------------
    assert margin == Margin(left=0.5, right=0.5, top=0.5, bottom=0.5)
    assert margin.width == 1.0
    assert margin.height == 1.0
