"""Test-only leaf element that records how it was drawn."""

from mpl_composite.elements import Element, Layout
from mpl_composite.geometry import XYZ


class Probe(Element):
    """Leaf element with declared size that records the layout it was drawn with."""

    def __init__(self, x_size: float = 1.0, y_size: float = 1.0, z_size: float = 1.0):
        self._size = XYZ(x_size, y_size, z_size)
        self.drawn_with: Layout | None = None

    def measure(self) -> XYZ:
        return self._size

    def draw(self, layout: Layout) -> None:
        self.drawn_with = layout
