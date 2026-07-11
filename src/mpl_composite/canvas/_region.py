"""A rectangular block of the shared Axes assigned to one element."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from mpl_composite.geometry import XYZRange


class LayoutError(Exception):
    """A placement produced a region outside its parent — a framework or element-size bug."""


@dataclass(frozen=True)
class Region:
    """A rectangular x/y/z block of the shared Axes, in axis coordinates."""

    ax: Axes
    xyz: XYZRange

    def sub_region(self, xyz: XYZRange) -> Region:
        """Construct a child block on the same Axes.

        Raises:
            LayoutError: If the child block is not contained in this one — the
                safety net that turns layout bugs into loud failures.
        """
        if not self.xyz.contains(xyz):
            raise LayoutError(f"sub-region {xyz} is not contained in parent region {self.xyz}.")
        return Region(ax=self.ax, xyz=xyz)
