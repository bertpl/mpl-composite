"""The Element ABC: a node in the figure tree with the measure -> place -> draw lifecycle."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from mpl_composite.canvas import Canvas
from mpl_composite.geometry import Range, XYZRange
from mpl_composite.style import LineStyle
from mpl_composite.transforms import Transform, XYZTransform

from ._layout import Layout

if TYPE_CHECKING:
    from mpl_composite.canvas import Region
    from mpl_composite.geometry import XYZ

_DEBUG_BOUNDARY_STYLE = LineStyle(color=(0.0, 0.0, 0.0), style=":", width=0.5)


class Element(ABC):
    """A node in the figure tree. Lifecycle: measure() -> place() -> draw().

    measure() is pure; place() returns an immutable Layout; draw() consumes it.
    Compose the tree first, then render — an element's size must not change
    after placement (guaranteed by Layout's immutability, not by caching).
    Only CompositeFigure.render() runs the pipeline in normal use.
    """

    # --------------------------------------------------------------------------
    #  Lifecycle
    # --------------------------------------------------------------------------
    @abstractmethod
    def measure(self) -> XYZ:
        """Return this element's (x, y, z) size in layout units. Pure."""

    def place(self, region: Region) -> Layout:
        """Build the canvas from the coordinate hooks and place any children."""
        plot = self._plot_ranges(self.measure())
        canvas = Canvas(region, self._transforms(plot, region))
        return Layout(canvas=canvas, children=self._place_children(canvas))

    @abstractmethod
    def draw(self, layout: Layout) -> None:
        """Draw this element (and its children) through layout.canvas."""

    # --------------------------------------------------------------------------
    #  Coordinate hooks (override to customize)
    # --------------------------------------------------------------------------
    def _plot_ranges(self, size: XYZ) -> XYZRange:
        """Plot-coordinate ranges of this element; default (0..x, 0..y, 0..z)."""
        return XYZRange(x=Range(0.0, size.x), y=Range(0.0, size.y), z=Range(0.0, size.z))

    def _transforms(self, plot: XYZRange, region: Region) -> XYZTransform:
        """Plot->axis transforms; default all-linear, y bottom-up (no reversal)."""
        return XYZTransform(
            x=Transform.linear(plot.x, region.xyz.x),
            y=Transform.linear(plot.y, region.xyz.y),
            z=Transform.linear(plot.z, region.xyz.z),
        )

    def _place_children(self, canvas: Canvas) -> tuple[Layout, ...]:
        """Place child elements; default: no children."""
        return ()

    # --------------------------------------------------------------------------
    #  Debugging
    # --------------------------------------------------------------------------
    def draw_debug_boundaries(self, layout: Layout, *, alpha: float = 0.8) -> None:
        """Dotted outline of this element's box (containers recurse with fading alpha)."""
        canvas = layout.canvas
        canvas.plot(
            x=[canvas.x.min, canvas.x.max, canvas.x.max, canvas.x.min, canvas.x.min],
            y=[canvas.y.min, canvas.y.min, canvas.y.max, canvas.y.max, canvas.y.min],
            style=_DEBUG_BOUNDARY_STYLE.modify(alpha=alpha, zorder=canvas.z.max),
        )
