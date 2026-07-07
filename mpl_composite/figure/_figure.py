"""The root element: owns the matplotlib Figure and the one invisible Axes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from matplotlib import pyplot as plt

from mpl_composite.canvas import Region
from mpl_composite.elements import Composite
from mpl_composite.geometry import Range, XYZRange

if TYPE_CHECKING:
    from matplotlib.figure import Figure


class CompositeFigure(Composite):
    """Root of the element tree: owns the matplotlib Figure and its one invisible Axes.

    render() runs the whole measure -> place -> draw lifecycle: figure/axes
    creation, chrome hiding, inch sizing from measured content. Subclass,
    compose in __init__, call render().
    """

    def __init__(self, *, fig_inch_per_unit: float = 8.0) -> None:
        """Set the layout-unit-to-inches conversion factor of the rendered figure."""
        super().__init__()
        self._fig_inch_per_unit = fig_inch_per_unit

    def render(self, *, debug_boundaries: bool = False) -> Figure:
        """Run the full lifecycle and return the rendered Figure.

        Args:
            debug_boundaries: Draw dotted outlines of every element's box —
                cheap and invaluable while composing.

        Raises:
            ValueError: When the figure is empty (zero x or y size).
        """
        size = self.measure()
        if size.x <= 0 or size.y <= 0:
            raise ValueError(f"cannot render an empty figure (measured size: {size.x} x {size.y}).")

        # --- create the one invisible Axes ---------------
        fig, ax = plt.subplots(1, 1)
        ax.set_xlim(0.0, size.x)
        ax.set_ylim(0.0, size.y)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.set_size_inches(size.x * self._fig_inch_per_unit, size.y * self._fig_inch_per_unit)

        # --- place & draw --------------------------------
        region = Region(
            ax=ax,
            xyz=XYZRange(x=Range(0.0, size.x), y=Range(0.0, size.y), z=Range(0.0, size.z)),
        )
        layout = self.place(region)
        self.draw(layout)
        if debug_boundaries:
            self.draw_debug_boundaries(layout)

        fig.tight_layout()
        return fig
