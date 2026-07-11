"""Pure layout geometry: intervals, per-dimension bundles, grids, alignment. No matplotlib."""

from ._alignment import HAlign, Margin, VAlign
from ._grid import LinearGrid
from ._range import Range
from ._xyz import XYZ, XYZRange

__all__ = ["XYZ", "HAlign", "LinearGrid", "Margin", "Range", "VAlign", "XYZRange"]
