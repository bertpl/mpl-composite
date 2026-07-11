"""Internal axis-bar elements: drawn ticks, tick labels, and the axis label.

Both bars bind their data dimension through PlotAxis.transform(), so tick
positions land exactly where the plot area maps the same values — log and
lin-log axes included. A bar's thickness is chosen by PlotAxes as a fraction
of the plot dimension it hangs off; internally the thickness splits into a
tick-mark band, a tick-label band, and (when the axis has a label) an
axis-label band.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mpl_composite.elements import Element
from mpl_composite.geometry import XYZ, HAlign, Range, VAlign, XYZRange
from mpl_composite.transforms import Transform, XYZTransform

if TYPE_CHECKING:
    from mpl_composite.axis import PlotAxis
    from mpl_composite.canvas import Region
    from mpl_composite.elements import Layout
    from mpl_composite.style import Theme

# Relative weights of the bands an axis bar splits its thickness into.
_TICK_BAND = 0.03  # major tick-mark length; minor marks get half
_TICK_LABEL_BAND = 0.07
_AXIS_LABEL_BAND = 0.09
_MINOR_LABEL_SCALE = 0.75  # minor tick-label size, relative to the major labels


def bar_thickness(plot_size: float, *, labeled: bool) -> float:
    """Thickness of an axis bar, as the banded fraction of the plot dimension it hangs off."""
    return plot_size * (_TICK_BAND + _TICK_LABEL_BAND + (_AXIS_LABEL_BAND if labeled else 0.0))


def _bands(thickness: float, *, labeled: bool) -> tuple[float, float, float]:
    """Split a bar thickness into (tick, tick-label, axis-label) band sizes."""
    total = _TICK_BAND + _TICK_LABEL_BAND + (_AXIS_LABEL_BAND if labeled else 0.0)
    scale = thickness / total
    return _TICK_BAND * scale, _TICK_LABEL_BAND * scale, (_AXIS_LABEL_BAND * scale if labeled else 0.0)


# ==================================================================================================
#  _XAxisBar
# ==================================================================================================
class _XAxisBar(Element):
    """Ticks, tick labels, and the axis label below the plot area."""

    def __init__(self, axis: PlotAxis, x_size: float, y_size: float, theme: Theme) -> None:
        """Bind the bar to its axis and box; x_size matches the plot area's width."""
        self._axis = axis
        self._x_size = x_size
        self._y_size = y_size
        self._theme = theme

    def measure(self) -> XYZ:
        """The declared box; no z extent."""
        return XYZ(self._x_size, self._y_size, 0.0)

    def _plot_ranges(self, size: XYZ) -> XYZRange:
        """X runs in data values; y is local bar thickness (plot edge at the top)."""
        return XYZRange(x=self._axis.range, y=Range(0.0, size.y), z=Range(0.0, size.z))

    def _transforms(self, plot: XYZRange, region: Region) -> XYZTransform:
        """Bind x through the axis scale so ticks align with the plot area."""
        return XYZTransform(
            x=self._axis.transform(region.xyz.x),
            y=Transform.linear(plot.y, region.xyz.y),
            z=Transform.linear(plot.z, region.xyz.z),
        )

    def draw(self, layout: Layout) -> None:
        """Tick marks down from the plot edge, labels below them, axis label at the bottom."""
        canvas = layout.canvas
        ticks = self._axis.ticks
        tick_band, label_band, axis_band = _bands(self._y_size, labeled=bool(self._axis.label))
        y_top = canvas.y.max

        # --- tick marks -----------------------------------
        for position in ticks.major:
            canvas.vline(position, self._theme.tick, y_min=y_top - tick_band, y_max=y_top)
        for position in ticks.minor:
            canvas.vline(position, self._theme.tick, y_min=y_top - 0.5 * tick_band, y_max=y_top)

        # --- tick labels ----------------------------------
        major_style = self._theme.text_tick_label
        minor_style = major_style.modify(size=_MINOR_LABEL_SCALE * major_style.size)
        y_label = y_top - tick_band - 0.5 * label_band
        for position, label in zip(ticks.major, ticks.major_labels, strict=True):
            canvas.text(position, y_label, label, major_style, h_align=HAlign.CENTER)
        for position, label in zip(ticks.minor, ticks.minor_labels, strict=True):
            if label:
                canvas.text(position, y_label, label, minor_style, h_align=HAlign.CENTER)

        # --- axis label -----------------------------------
        if self._axis.label:
            y_axis_label = y_top - tick_band - label_band - 0.5 * axis_band
            canvas.text(self._axis.mid_point, y_axis_label, self._axis.label, self._theme.text, h_align=HAlign.CENTER)


# ==================================================================================================
#  _YAxisBar
# ==================================================================================================
class _YAxisBar(Element):
    """Ticks, tick labels, and the (rotated) axis label left of the plot area."""

    def __init__(self, axis: PlotAxis, x_size: float, y_size: float, theme: Theme) -> None:
        """Bind the bar to its axis and box; y_size matches the plot area's height."""
        self._axis = axis
        self._x_size = x_size
        self._y_size = y_size
        self._theme = theme

    def measure(self) -> XYZ:
        """The declared box; no z extent."""
        return XYZ(self._x_size, self._y_size, 0.0)

    def _plot_ranges(self, size: XYZ) -> XYZRange:
        """Y runs in data values; x is local bar thickness (plot edge at the right)."""
        return XYZRange(x=Range(0.0, size.x), y=self._axis.range, z=Range(0.0, size.z))

    def _transforms(self, plot: XYZRange, region: Region) -> XYZTransform:
        """Bind y through the axis scale so ticks align with the plot area."""
        return XYZTransform(
            x=Transform.linear(plot.x, region.xyz.x),
            y=self._axis.transform(region.xyz.y),
            z=Transform.linear(plot.z, region.xyz.z),
        )

    def draw(self, layout: Layout) -> None:
        """Tick marks left from the plot edge, labels beside them, rotated axis label at the far left."""
        canvas = layout.canvas
        ticks = self._axis.ticks
        tick_band, label_band, axis_band = _bands(self._x_size, labeled=bool(self._axis.label))
        x_right = canvas.x.max

        # --- tick marks -----------------------------------
        for position in ticks.major:
            canvas.hline(position, self._theme.tick, x_min=x_right - tick_band, x_max=x_right)
        for position in ticks.minor:
            canvas.hline(position, self._theme.tick, x_min=x_right - 0.5 * tick_band, x_max=x_right)

        # --- tick labels ----------------------------------
        major_style = self._theme.text_tick_label
        minor_style = major_style.modify(size=_MINOR_LABEL_SCALE * major_style.size)
        x_label = x_right - tick_band - 0.1 * label_band
        for position, label in zip(ticks.major, ticks.major_labels, strict=True):
            canvas.text(x_label, position, label, major_style, h_align=HAlign.RIGHT, v_align=VAlign.CENTER)
        for position, label in zip(ticks.minor, ticks.minor_labels, strict=True):
            if label:
                canvas.text(x_label, position, label, minor_style, h_align=HAlign.RIGHT, v_align=VAlign.CENTER)

        # --- axis label -----------------------------------
        if self._axis.label:
            x_axis_label = x_right - tick_band - label_band - 0.5 * axis_band
            canvas.text(
                x_axis_label,
                self._axis.mid_point,
                self._axis.label,
                self._theme.text.modify(rotation_deg=90.0),
                h_align=HAlign.CENTER,
                v_align=VAlign.CENTER,
            )
