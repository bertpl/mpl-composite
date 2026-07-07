"""The drawing surface elements see: plt.Axes-like methods in element-local plot coordinates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from matplotlib.patches import Rectangle

from mpl_composite.geometry import HAlign, Range, VAlign, XYZRange
from mpl_composite.style import TextStyle

from ._measure import artist_size
from ._region import Region

if TYPE_CHECKING:
    from mpl_composite.style import LineStyle
    from mpl_composite.transforms import Transform, XYZTransform

_DEFAULT_TEXT_STYLE = TextStyle()

# HAlign/VAlign -> matplotlib ha/va strings (FILL has no matplotlib analog; center reads best).
_MPL_HA = {HAlign.LEFT: "left", HAlign.CENTER: "center", HAlign.RIGHT: "right", HAlign.FILL: "center"}
_MPL_VA = {VAlign.TOP: "top", VAlign.CENTER: "center", VAlign.BOTTOM: "bottom", VAlign.FILL: "center"}

# Reference text used to estimate rotated-text geometry: the delta between a
# short and a long run isolates the advance direction from constant padding.
_ASPECT_PROBE_SHORT = "xxx"
_ASPECT_PROBE_LONG = "xxxxxxxxxxxxxx"


class Canvas:
    """plt.Axes-like drawing API in an element's local plot coordinates.

    Maps plot -> axis coordinates through its XYZTransform; the only drawing
    surface elements ever see. zorder values (in styles or arguments) are in
    the element's local z range and are transformed like any coordinate.
    """

    # --------------------------------------------------------------------------
    #  Constructor & coordinate info
    # --------------------------------------------------------------------------
    def __init__(self, region: Region, transforms: XYZTransform) -> None:
        """Bind the canvas to its Axes region and per-dimension transforms."""
        self._region = region
        self._trans = transforms

    @property
    def x(self) -> Range:
        """Plot-coordinate x range."""
        return self._trans.x.plot_range

    @property
    def y(self) -> Range:
        """Plot-coordinate y range."""
        return self._trans.y.plot_range

    @property
    def z(self) -> Range:
        """Plot-coordinate z range."""
        return self._trans.z.plot_range

    @property
    def top(self) -> float:
        """Plot y value at the visual top edge (reversal-aware)."""
        return self.y.min if self._trans.y.is_reverse else self.y.max

    @property
    def bottom(self) -> float:
        """Plot y value at the visual bottom edge (reversal-aware)."""
        return self.y.max if self._trans.y.is_reverse else self.y.min

    @property
    def left(self) -> float:
        """Plot x value at the visual left edge (reversal-aware)."""
        return self.x.max if self._trans.x.is_reverse else self.x.min

    @property
    def right(self) -> float:
        """Plot x value at the visual right edge (reversal-aware)."""
        return self.x.min if self._trans.x.is_reverse else self.x.max

    def aspect_ratio(self) -> float:
        """Axis-coordinate size of 1 plot unit in x over the same in y (angle-true drawing).

        Raises:
            ValueError: On a non-linear x or y transform (delta-based operation).
        """
        self._require_linear("aspect_ratio", self._trans.x, self._trans.y)
        x_scale = self._trans.x.ax_range.size / self._trans.x.plot_range.size
        y_scale = self._trans.y.ax_range.size / self._trans.y.plot_range.size
        return x_scale / y_scale

    def sub_region(self, xyz: XYZRange) -> Region:
        """Convert a plot-coordinate block into a child's axis-coordinate Region."""
        return self._region.sub_region(
            XYZRange(
                x=self._trans.x.map_range(xyz.x),
                y=self._trans.y.map_range(xyz.y),
                z=self._trans.z.map_range(xyz.z),
            )
        )

    # --------------------------------------------------------------------------
    #  Drawing - lines
    # --------------------------------------------------------------------------
    def plot(self, x: float | list[float], y: float | list[float], style: LineStyle) -> None:
        """Plot a line (with markers) in plot coordinates."""
        z_ax = self._trans.z(style.zorder)
        style.modify(zorder=z_ax).plot(self._region.ax, self._trans.x(x), self._trans.y(y))

    def hline(
        self,
        y: float | list[float],
        style: LineStyle,
        x_min: float | None = None,
        x_max: float | None = None,
    ) -> None:
        """Horizontal line(s) at plot y value(s), spanning [x_min, x_max] (default: the full x range)."""
        y_list = [y] if isinstance(y, int | float) else y
        x_span = [self.x.min if x_min is None else x_min, self.x.max if x_max is None else x_max]
        for y_el in y_list:
            self.plot(x_span, [y_el, y_el], style)

    def vline(
        self,
        x: float | list[float],
        style: LineStyle,
        y_min: float | None = None,
        y_max: float | None = None,
    ) -> None:
        """Vertical line(s) at plot x value(s), spanning [y_min, y_max] (default: the full y range)."""
        x_list = [x] if isinstance(x, int | float) else x
        y_span = [self.y.min if y_min is None else y_min, self.y.max if y_max is None else y_max]
        for x_el in x_list:
            self.plot([x_el, x_el], y_span, style)

    def plot_sample(self, x_min: float, x_max: float, y: float, style: LineStyle) -> None:
        """One horizontal sample segment with a single centered marker — for legend swatches."""
        z_ax = self._trans.z(style.zorder)
        x_ax = self._trans.x([x_min, x_max])
        style.modify(zorder=z_ax).plot_sample(self._region.ax, x_min=x_ax[0], x_max=x_ax[1], y=self._trans.y(y))

    # --------------------------------------------------------------------------
    #  Drawing - shapes
    # --------------------------------------------------------------------------
    def rectangle(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        *,
        fill_color: str | tuple[float, float, float],
        edge_style: LineStyle | None = None,
        zorder: float = 0.0,
    ) -> None:
        """Axis-aligned filled rectangle in plot coordinates, with an optional edge line style."""
        x_ax = sorted(self._trans.x([x_min, x_max]))
        y_ax = sorted(self._trans.y([y_min, y_max]))
        rect = Rectangle(
            xy=(x_ax[0], y_ax[0]),
            width=x_ax[1] - x_ax[0],
            height=y_ax[1] - y_ax[0],
            facecolor=fill_color,
            edgecolor=edge_style.color if edge_style else None,
            linewidth=edge_style.width if edge_style else 0.0,
            zorder=self._trans.z(zorder),
        )
        self._region.ax.add_patch(rect)

    # --------------------------------------------------------------------------
    #  Drawing - text
    # --------------------------------------------------------------------------
    def text(
        self,
        x: float,
        y: float,
        s: str,
        style: TextStyle = _DEFAULT_TEXT_STYLE,
        *,
        h_align: HAlign = HAlign.LEFT,
        v_align: VAlign = VAlign.CENTER,
        zorder: float | None = None,
    ) -> None:
        """Text at a plot-coordinate anchor point (default z: the middle of the local z range)."""
        z = self.z.center if zorder is None else zorder
        self._region.ax.text(
            x=self._trans.x(x),
            y=self._trans.y(y),
            s=s,
            ha=_MPL_HA[h_align],
            va=_MPL_VA[v_align],
            fontsize=style.size,
            fontweight=style.weight.value,
            color=style.color,
            rotation=style.rotation_deg,
            zorder=self._trans.z(z),
        )

    def text_size(self, s: str, style: TextStyle) -> tuple[float, float]:
        """(width, height) of the rendered text, in plot coordinates.

        Measures via a temporary artist and the renderer, then converts the
        axis-coordinate deltas back to plot coordinates.

        Raises:
            ValueError: On a non-linear x or y transform (delta-based operation).
        """
        self._require_linear("text_size", self._trans.x, self._trans.y)
        ax = self._region.ax
        artist = ax.text(0, 0, s, fontsize=style.size, fontweight=style.weight.value, rotation=style.rotation_deg)
        w_ax, h_ax = artist_size(ax.figure, ax, artist)
        artist.remove()

        w_plot = w_ax * (self._trans.x.plot_range.size / self._trans.x.ax_range.size)
        h_plot = h_ax * (self._trans.y.plot_range.size / self._trans.y.ax_range.size)
        return abs(w_plot), abs(h_plot)

    def rotated_text_aspect(self, rotation_deg: float, *, ref_size: float = 10.0) -> float:
        """x-per-y advance ratio of rotated text — for leader lines parallel to labels.

        Raises:
            ValueError: On a non-linear x or y transform (delta-based operation).
        """
        style = TextStyle(size=ref_size, rotation_deg=rotation_deg)
        w_short, h_short = self.text_size(_ASPECT_PROBE_SHORT, style)
        w_long, h_long = self.text_size(_ASPECT_PROBE_LONG, style)
        return abs(w_long - w_short) / abs(h_long - h_short)

    # --------------------------------------------------------------------------
    #  Internal
    # --------------------------------------------------------------------------
    @staticmethod
    def _require_linear(operation: str, *transforms: Transform) -> None:
        """Raise when a delta-based operation runs on a non-linear transform.

        Size conversion between coordinate spaces is position-dependent on
        non-linear transforms, so the result would be silently wrong.

        Raises:
            ValueError: If any given transform is non-linear.
        """
        if any(not t.is_linear() for t in transforms):
            raise ValueError(f"Canvas.{operation} requires linear x/y transforms (delta-based operation).")
