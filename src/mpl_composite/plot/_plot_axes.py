"""PlotAxes: a classic x/y plot assembled from internal elements."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from mpl_composite.elements import Composite, Element, Text
from mpl_composite.geometry import XYZ, Range, XYZRange
from mpl_composite.style import DEFAULT_THEME
from mpl_composite.transforms import Transform, XYZTransform

from ._axis_bars import _XAxisBar, _YAxisBar, bar_thickness

if TYPE_CHECKING:
    from collections.abc import Callable

    from mpl_composite.axis import PlotAxis
    from mpl_composite.canvas import Canvas, Region
    from mpl_composite.elements import Layout
    from mpl_composite.style import Theme

_TITLE_BAND = 0.06  # title box height, as a fraction of the plot height


# ==================================================================================================
#  _PlotArea
# ==================================================================================================
class _PlotArea(Element):
    """The framed data region: grid + border from the two axes, content via a draw callback.

    Its canvas is in DATA coordinates: x/y bind through the axes' scales, so
    the owner's draw_plot() plots values directly. The local z range is (0, 1):
    grid lines sit just above 0, the frame at 1; content styles use zorder
    in between (the LineStyle default of 0 lands on the grid level — fine for
    ordinary curves).
    """

    def __init__(
        self,
        x_axis: PlotAxis,
        y_axis: PlotAxis,
        draw_fn: Callable[[Canvas], None],
        x_size: float,
        y_size: float,
        theme: Theme,
    ) -> None:
        """Bind the area to its axes, owner callback, box, and theme."""
        self._x_axis = x_axis
        self._y_axis = y_axis
        self._draw_fn = draw_fn
        self._x_size = x_size
        self._y_size = y_size
        self._theme = theme

    def measure(self) -> XYZ:
        """The declared box, with a unit z extent for content layering."""
        return XYZ(self._x_size, self._y_size, 1.0)

    def _plot_ranges(self, size: XYZ) -> XYZRange:
        """X and y run in data values; z is the local (0, 1) layering range."""
        return XYZRange(x=self._x_axis.range, y=self._y_axis.range, z=Range(0.0, size.z))

    def _transforms(self, plot: XYZRange, region: Region) -> XYZTransform:
        """Bind x and y through the axes' scales (log-aware); z stays linear."""
        return XYZTransform(
            x=self._x_axis.transform(region.xyz.x),
            y=self._y_axis.transform(region.xyz.y),
            z=Transform.linear(plot.z, region.xyz.z),
        )

    def draw(self, layout: Layout) -> None:
        """Grid lines at the ticks, the owner's plot content, and the frame on top."""
        canvas = layout.canvas
        theme = self._theme

        # --- grid -----------------------------------------
        grid_minor = theme.grid_minor.modify(zorder=0.01)
        grid_major = theme.grid_major.modify(zorder=0.02)
        canvas.vline(list(self._x_axis.ticks.minor), grid_minor)
        canvas.hline(list(self._y_axis.ticks.minor), grid_minor)
        canvas.vline(list(self._x_axis.ticks.major), grid_major)
        canvas.hline(list(self._y_axis.ticks.major), grid_major)

        # --- content --------------------------------------
        self._draw_fn(canvas)

        # --- frame ----------------------------------------
        frame = theme.border_major.modify(zorder=1.0)
        x, y = canvas.x, canvas.y
        canvas.plot([x.min, x.max, x.max, x.min, x.min], [y.min, y.min, y.max, y.max, y.min], frame)


# ==================================================================================================
#  PlotAxes
# ==================================================================================================
class PlotAxes(Composite):
    """A classic x/y plot: title, plot area with grid, drawn x & y axis bars.

    Subclass and override draw_plot(); it receives a canvas in DATA
    coordinates (x per x_axis, y per y_axis, log-aware).
    """

    def __init__(
        self,
        x_axis: PlotAxis,
        y_axis: PlotAxis,
        *,
        plot_width: float,
        plot_height: float,
        title: str = "",
        theme: Theme = DEFAULT_THEME,
    ) -> None:
        """Assemble the internal grid: title row, y bar column, plot area, x bar row.

        Args:
            x_axis: The horizontal data axis.
            y_axis: The vertical data axis.
            plot_width: Width of the data area (layout units); bars and title add to it.
            plot_height: Height of the data area (layout units).
            title: Optional title above the plot.
            theme: Style vocabulary for grid, frame, ticks, and text.

        Raises:
            ValueError: On a non-positive plot size.
        """
        if plot_width <= 0 or plot_height <= 0:
            raise ValueError(f"plot sizes must be > 0 (here: ({plot_width}, {plot_height})).")
        super().__init__()
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.theme = theme

        i_row = 0
        if title:
            self.add(i_row, 1, Text(plot_width, _TITLE_BAND * plot_height, title, style=theme.text_title))
            i_row += 1
        self.add(i_row, 0, _YAxisBar(y_axis, bar_thickness(plot_width, labeled=bool(y_axis.label)), plot_height, theme))
        self.add(i_row, 1, _PlotArea(x_axis, y_axis, self.draw_plot, plot_width, plot_height, theme))
        self.add(
            i_row + 1, 1, _XAxisBar(x_axis, plot_width, bar_thickness(plot_height, labeled=bool(x_axis.label)), theme)
        )

    @abstractmethod
    def draw_plot(self, canvas: Canvas) -> None:
        """Draw the plot content in data coordinates."""
