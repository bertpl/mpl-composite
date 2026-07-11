"""Line + marker style value object."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

    from matplotlib.axes import Axes


@dataclass(frozen=True)
class LineStyle:
    """Line + marker style; knows how to render itself onto a matplotlib Axes.

    The zorder field is expressed in the drawing element's local z range and is
    transformed like any coordinate when drawn through a Canvas.
    """

    color: str | tuple[float, float, float] = (0.0, 0.0, 0.0)
    width: float = 1.0
    style: str | tuple[float, tuple[float, ...]] = "-"
    line_enabled: bool = True
    marker: str = ""
    marker_size: float = 1.0
    marker_filled: bool = True
    alpha: float = 1.0
    zorder: float = 0.0

    # --------------------------------------------------------------------------
    #  Modifiers
    # --------------------------------------------------------------------------
    def modify(self, **overrides: object) -> LineStyle:
        """Copy with the given fields replaced (dataclasses.replace semantics)."""
        return dataclasses.replace(self, **overrides)  # type: ignore[arg-type]

    # --------------------------------------------------------------------------
    #  matplotlib kwargs
    # --------------------------------------------------------------------------
    def _line_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for the line part of an ax.plot call."""
        if not self.line_enabled:
            return {"linewidth": 0.0}
        return {
            "color": self.color,
            "linewidth": self.width,
            "linestyle": self.style,
            "alpha": self.alpha,
            "zorder": self.zorder,
        }

    def _marker_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for the marker part of an ax.plot call."""
        if (self.alpha < 1.0) and isinstance(self.color, tuple):
            color: str | tuple[float, ...] = (*self.color, self.alpha)
        else:
            color = self.color

        return {
            "marker": self.marker,
            "markersize": self.marker_size,
            "markerfacecolor": color if self.marker_filled else (1.0, 1.0, 1.0, self.alpha),
            "markeredgecolor": color,
            "markeredgewidth": self.width,
            "zorder": self.zorder,
        }

    # --------------------------------------------------------------------------
    #  Rendering
    # --------------------------------------------------------------------------
    def plot(self, ax: Axes, x: float | Iterable[float], y: float | Iterable[float]) -> None:
        """Plot a line (with markers) on the Axes; a scalar x or y is broadcast to the other's length.

        Raises:
            ValueError: If x and y have incompatible lengths.
        """
        x_list = [float(x)] if isinstance(x, int | float) else [float(el) for el in x]
        y_list = [float(y)] if isinstance(y, int | float) else [float(el) for el in y]
        if len(x_list) == 1:
            x_list = x_list * len(y_list)
        elif len(y_list) == 1:
            y_list = y_list * len(x_list)
        elif len(x_list) != len(y_list):
            raise ValueError(f"x and y must have equal length or one must be scalar ({len(x_list)} vs {len(y_list)}).")

        ax.plot(x_list, y_list, **(self._line_kwargs() | self._marker_kwargs()))

    def plot_sample(self, ax: Axes, x_min: float, x_max: float, y: float) -> None:
        """Plot one horizontal sample segment with a single centered marker — for legend swatches."""
        ax.plot([x_min, x_max], [y, y], **self._line_kwargs())
        ax.plot(0.5 * (x_min + x_max), y, **self._marker_kwargs())
