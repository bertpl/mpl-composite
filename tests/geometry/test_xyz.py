import pytest

from mpl_composite.geometry import XYZ, Range, XYZRange


def test_xyz_fields() -> None:
    # --- act --------------------------
    size = XYZ(1.0, 2.0, 3.0)

    # --- assert -----------------------
    assert (size.x, size.y, size.z) == (1.0, 2.0, 3.0)


def test_xyz_range_size() -> None:
    # --- arrange ----------------------
    block = XYZRange(x=Range(0.0, 2.0), y=Range(1.0, 5.0), z=Range(-1.0, 0.0))

    # --- act --------------------------
    size = block.size

    # --- assert -----------------------
    assert size == XYZ(2.0, 4.0, 1.0)


@pytest.mark.parametrize(
    "inner, expected",
    [
        (XYZRange(Range(1.0, 2.0), Range(1.0, 2.0), Range(1.0, 2.0)), True),
        (XYZRange(Range(0.0, 10.0), Range(0.0, 10.0), Range(0.0, 10.0)), True),  # identical block
        (XYZRange(Range(-1.0, 2.0), Range(1.0, 2.0), Range(1.0, 2.0)), False),  # x sticks out
        (XYZRange(Range(1.0, 2.0), Range(1.0, 11.0), Range(1.0, 2.0)), False),  # y sticks out
        (XYZRange(Range(1.0, 2.0), Range(1.0, 2.0), Range(-1.0, 2.0)), False),  # z sticks out
    ],
)
def test_xyz_range_contains(inner: XYZRange, expected: bool) -> None:
    # --- arrange ----------------------
    outer = XYZRange(Range(0.0, 10.0), Range(0.0, 10.0), Range(0.0, 10.0))

    # --- act / assert -----------------
    assert outer.contains(inner) is expected
