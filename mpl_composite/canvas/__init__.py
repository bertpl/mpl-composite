"""The matplotlib-aware drawing layer: regions of the shared Axes and the element canvas."""

from ._canvas import Canvas
from ._measure import artist_size
from ._region import LayoutError, Region

__all__ = ["Canvas", "LayoutError", "Region", "artist_size"]
