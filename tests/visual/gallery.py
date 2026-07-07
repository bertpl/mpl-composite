"""The gallery of figures pinned by visual-regression baselines.

Every entry renders through the full measure -> place -> draw lifecycle; new
element families add a figure here so their visual output gets pinned.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from mpl_composite import (
    Composite,
    CompositeFigure,
    HAlign,
    Legend,
    LegendEntry,
    LineStyle,
    PlotAxes,
    PlotAxis,
    ScaleLog,
    Spacer,
    Text,
    TextStyle,
    VAlign,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from mpl_composite.canvas import Canvas


def demo_composite() -> CompositeFigure:
    """Title over a 2x2 inner grid with spacers: the v0.1.0 engine smoke figure."""
    fig = CompositeFigure(fig_inch_per_unit=4.0)
    fig.add(0, 0, Text(1.0, 0.15, "Demo title"))
    inner = Composite()
    inner.add(0, 0, Text(0.4, 0.1, "top left"))
    inner.add(0, 1, Spacer(0.1, 0.1))
    inner.add(1, 0, Spacer(0.1, 0.1))
    inner.add(1, 1, Text(0.4, 0.1, "bottom right"))
    fig.add(1, 0, inner, margin=0.05)
    return fig


_CURVE_STYLE = LineStyle(color=(0.2, 0.3, 0.8))
_SAMPLE_STYLE = LineStyle(color=(0.8, 0.3, 0.2), line_enabled=False, marker="o", marker_size=3.0)


class _ScatterDemo(PlotAxes):
    """Worked PlotAxes subclass: curves, scattered markers, an annotation, and a legend."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Assemble the plot and anchor a legend on top of its plot area."""
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        legend = Legend(
            [LegendEntry("power law", _CURVE_STYLE), LegendEntry("samples", _SAMPLE_STYLE)],
            row_height=0.04,
        )
        self.add(1, 1, legend, h_align=HAlign.RIGHT, v_align=VAlign.TOP, margin=0.015)

    def draw_plot(self, canvas: Canvas) -> None:
        """Two curves in data coordinates plus a pointed-out sample."""
        x = [0.5 + 0.05 * i for i in range(191)]
        canvas.plot(x, [10.0 * v**-1.5 for v in x], _CURVE_STYLE)
        canvas.plot(
            x[::10],
            [3.0 * math.exp(-((v - 5.0) ** 2)) + 0.1 for v in x[::10]],
            _SAMPLE_STYLE,
        )
        canvas.text(5.0, 3.5, "peak", TextStyle(size=8.0), zorder=0.5)


def plot_axes_demo() -> CompositeFigure:
    """A classic x/y plot: linear x, log y, title, axis labels, grid."""
    fig = CompositeFigure(fig_inch_per_unit=6.0)
    fig.add(
        0,
        0,
        _ScatterDemo(
            PlotAxis.from_range(0.5, 10.0, label="x value"),
            PlotAxis.from_range(0.05, 50.0, scale=ScaleLog(), label="y value"),
            plot_width=1.0,
            plot_height=0.7,
            title="Scatter demo",
        ),
        margin=0.02,
    )
    return fig


GALLERY: dict[str, Callable[[], CompositeFigure]] = {
    "demo_composite": demo_composite,
    "plot_axes_demo": plot_axes_demo,
}
