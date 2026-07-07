from unittest.mock import Mock

import pytest

from mpl_composite.canvas import LayoutError, Region
from mpl_composite.geometry import Range, XYZRange


def _block(x_max: float = 10.0, y_max: float = 10.0, z_max: float = 10.0) -> XYZRange:
    return XYZRange(x=Range(0.0, x_max), y=Range(0.0, y_max), z=Range(0.0, z_max))


def test_sub_region_keeps_the_same_axes() -> None:
    # --- arrange ----------------------
    ax = Mock()
    region = Region(ax=ax, xyz=_block())

    # --- act --------------------------
    child = region.sub_region(XYZRange(x=Range(1.0, 2.0), y=Range(3.0, 4.0), z=Range(0.0, 1.0)))

    # --- assert -----------------------
    assert child.ax is ax
    assert child.xyz.x == Range(1.0, 2.0)


def test_sub_region_rejects_escaping_block() -> None:
    # --- arrange ----------------------
    region = Region(ax=Mock(), xyz=_block())

    # --- act / assert -----------------
    with pytest.raises(LayoutError, match="not contained"):
        region.sub_region(XYZRange(x=Range(1.0, 11.0), y=Range(0.0, 1.0), z=Range(0.0, 1.0)))


def test_sub_region_tolerates_boundary_touching_blocks() -> None:
    # --- arrange ----------------------
    region = Region(ax=Mock(), xyz=_block())

    # --- act --------------------------
    child = region.sub_region(_block())  # identical block: allowed

    # --- assert -----------------------
    assert child.xyz == region.xyz
