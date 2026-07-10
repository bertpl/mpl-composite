"""Empty element that only occupies space."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mpl_composite.geometry import XYZ

from ._element import Element

if TYPE_CHECKING:
    from ._layout import Layout


class Spacer(Element):
    """Empty element that only occupies space in the layout grid."""

    def __init__(self, x_size: float, y_size: float) -> None:
        """Declare the occupied box.

        Raises:
            ValueError: On a negative size.
        """
        if x_size < 0 or y_size < 0:
            raise ValueError(f"Spacer sizes must be >= 0 (here: ({x_size}, {y_size})).")
        self._x_size = x_size
        self._y_size = y_size

    def measure(self) -> XYZ:
        """The declared box; no z extent."""
        return XYZ(self._x_size, self._y_size, 0.0)

    def draw(self, layout: Layout) -> None:
        """Nothing to draw."""
