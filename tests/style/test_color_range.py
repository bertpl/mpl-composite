import pytest

from mpl_composite.style import ColorRange


# ==================================================================================================
#  Construction & validation
# ==================================================================================================
@pytest.mark.parametrize(
    "stops, match",
    [
        (((0.0, (0.0, 0.0, 0.0)),), "at least 2"),
        (((1.0, (0.0, 0.0, 0.0)), (1.0, (1.0, 1.0, 1.0))), "strictly increasing"),
        (((2.0, (0.0, 0.0, 0.0)), (1.0, (1.0, 1.0, 1.0))), "strictly increasing"),
    ],
)
def test_rejects_invalid_stops(stops: tuple, match: str) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match=match):
        ColorRange(stops=stops)


# ==================================================================================================
#  Interpolation
# ==================================================================================================
@pytest.mark.parametrize(
    "v, expected",
    [
        (0.0, (0.0, 0.0, 0.0)),  # exact stop
        (1.0, (1.0, 0.0, 0.0)),
        (0.5, (0.5, 0.0, 0.0)),  # midpoint of first segment
        (1.5, (1.0, 0.5, 0.0)),  # midpoint of second segment
        (2.0, (1.0, 1.0, 0.0)),
        (-5.0, (0.0, 0.0, 0.0)),  # clamps below
        (99.0, (1.0, 1.0, 0.0)),  # clamps above
    ],
)
def test_at_interpolates_and_clamps(v: float, expected: tuple) -> None:
    # --- arrange ----------------------
    cr = ColorRange(stops=((0.0, (0.0, 0.0, 0.0)), (1.0, (1.0, 0.0, 0.0)), (2.0, (1.0, 1.0, 0.0))))

    # --- act / assert -----------------
    assert cr.at(v) == pytest.approx(expected)


def test_two_point_factory() -> None:
    # --- act --------------------------
    cr = ColorRange.two_point(0.0, (0.0, 0.0, 0.0), 10.0, (1.0, 1.0, 1.0))

    # --- assert -----------------------
    assert cr.at(5.0) == pytest.approx((0.5, 0.5, 0.5))
