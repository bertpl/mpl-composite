"""Renderer-based measurement of matplotlib artists."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.artist import Artist
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure, SubFigure


def artist_size(fig: Figure | SubFigure, ax: Axes, artist: Artist) -> tuple[float, float]:
    """Measure an artist's rendered size, in axis (data) coordinates.

    Uses the renderer's window extent (display pixels) converted back through
    the Axes data transform — the only reliable way to size text in matplotlib.

    Args:
        fig: The figure owning the renderer.
        ax: The Axes whose data coordinates the size is expressed in.
        artist: The (already added) artist to measure.

    Returns:
        (width, height) of the artist's bounding box in data coordinates.
    """
    # get_renderer exists on the Agg canvas (the backend this library measures on),
    # but not on the FigureCanvasBase type the stubs see.
    bbox = artist.get_window_extent(renderer=fig.canvas.get_renderer())  # ty: ignore[unresolved-attribute]
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([(bbox.x0, bbox.y0), (bbox.x1, bbox.y1)])
    return abs(float(x1) - float(x0)), abs(float(y1) - float(y0))
