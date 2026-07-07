import pytest

from mpl_composite.geometry import Range


# ==================================================================================================
#  Construction
# ==================================================================================================
def test_range_rejects_inverted_bounds() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="min <= max"):
        Range(1.0, 0.0)


def test_range_allows_degenerate_interval() -> None:
    # --- act --------------------------
    r = Range(2.0, 2.0)

    # --- assert -----------------------
    assert r.size == 0.0
    assert r.center == 2.0


# ==================================================================================================
#  Derived properties
# ==================================================================================================
@pytest.mark.parametrize(
    "r, size, center",
    [
        (Range(0.0, 1.0), 1.0, 0.5),
        (Range(-3.0, 5.0), 8.0, 1.0),
        (Range(-10.0, -4.0), 6.0, -7.0),
    ],
)
def test_range_size_center(r: Range, size: float, center: float) -> None:
    # --- assert -----------------------
    assert r.size == size
    assert r.center == center


# ==================================================================================================
#  at()
# ==================================================================================================
@pytest.mark.parametrize(
    "r, p, expected",
    [
        (Range(0.0, 10.0), 0.0, 0.0),
        (Range(0.0, 10.0), 1.0, 10.0),
        (Range(0.0, 10.0), 0.25, 2.5),
        (Range(-2.0, 2.0), 0.5, 0.0),
        (Range(0.0, 10.0), -0.5, -5.0),  # extrapolation is allowed
        (Range(0.0, 10.0), 1.5, 15.0),
    ],
)
def test_range_at(r: Range, p: float, expected: float) -> None:
    # --- act / assert -----------------
    assert r.at(p) == pytest.approx(expected)


# ==================================================================================================
#  contains()
# ==================================================================================================
@pytest.mark.parametrize(
    "r, value, expected",
    [
        (Range(0.0, 1.0), 0.5, True),
        (Range(0.0, 1.0), 0.0, True),
        (Range(0.0, 1.0), 1.0, True),
        (Range(0.0, 1.0), -0.1, False),
        (Range(0.0, 1.0), 1.1, False),
        # tolerance: barely outside is still inside
        (Range(0.0, 1.0), 1.0 + 1e-12, True),
        (Range(0.0, 1.0), -1e-12, True),
        # negative intervals get the same tolerance behavior
        (Range(-2.0, -1.0), -1.0 - 1e-12, True),
        (Range(-2.0, -1.0), -2.0 - 1e-12, True),
        (Range(-2.0, -1.0), -0.5, False),
        # large magnitudes: tolerance scales relatively
        (Range(0.0, 1e9), 1e9 + 0.1, True),
        (Range(0.0, 1e9), 1.1e9, False),
    ],
)
def test_range_contains_value(r: Range, value: float, expected: bool) -> None:
    # --- act / assert -----------------
    assert r.contains(value) is expected


@pytest.mark.parametrize(
    "outer, inner, expected",
    [
        (Range(0.0, 10.0), Range(2.0, 8.0), True),
        (Range(0.0, 10.0), Range(0.0, 10.0), True),
        (Range(0.0, 10.0), Range(-1.0, 5.0), False),
        (Range(0.0, 10.0), Range(5.0, 11.0), False),
        # tolerance applies to both endpoints
        (Range(0.0, 10.0), Range(-1e-12, 10.0 + 1e-12), True),
        (Range(-5.0, -1.0), Range(-5.0 - 1e-12, -1.0), True),
    ],
)
def test_range_contains_range(outer: Range, inner: Range, expected: bool) -> None:
    # --- act / assert -----------------
    assert outer.contains(inner) is expected


def test_range_contains_respects_explicit_tolerance() -> None:
    # --- arrange ----------------------
    r = Range(0.0, 1.0)

    # --- act / assert -----------------
    assert r.contains(1.005, tol=0.01)
    assert not r.contains(1.005, tol=1e-9)
