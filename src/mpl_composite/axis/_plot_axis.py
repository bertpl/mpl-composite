"""The immutable data-axis value object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mpl_composite.geometry import Range

from ._scale import Scale, ScaleLinear
from ._ticks import Ticks

if TYPE_CHECKING:
    from mpl_composite.transforms import Transform

_DEFAULT_SCALE = ScaleLinear()


@dataclass(frozen=True)
class PlotAxis:
    """A data axis: value range + ticks + scale + label. Immutable and shareable.

    Binding to a screen extent never mutates the axis: `transform()` produces a
    new Transform each time. All scale-kind dispatch is delegated to the Scale
    object — one PlotAxis class, no per-scale subclasses.
    """

    range: Range
    ticks: Ticks
    scale: Scale = _DEFAULT_SCALE
    label: str = ""

    # --------------------------------------------------------------------------
    #  Main API
    # --------------------------------------------------------------------------
    def transform(self, ax_range: Range, *, reverse: bool = False) -> Transform:
        """Bind this axis to an axis-coordinate range -> the plot->axis mapping (delegates to scale)."""
        return self.scale.transform(self.range, ax_range, reverse=reverse)

    @property
    def mid_point(self) -> float:
        """Visual center of the axis in data values (delegates to scale)."""
        return self.scale.mid_point(self.range)

    # --------------------------------------------------------------------------
    #  Factory methods
    # --------------------------------------------------------------------------
    @classmethod
    def from_range(
        cls,
        v_min: float,
        v_max: float,
        *,
        scale: Scale = _DEFAULT_SCALE,
        label: str = "",
        auto_ticks: bool = True,
    ) -> PlotAxis:
        """Range-first construction; ticks come from scale.ticks() when auto_ticks."""
        value_range = Range(v_min, v_max)
        ticks = scale.ticks(value_range) if auto_ticks else Ticks(major=(), major_labels=())
        return cls(range=value_range, ticks=ticks, scale=scale, label=label)

    @classmethod
    def from_ticks(
        cls,
        ticks: Ticks,
        *,
        scale: Scale = _DEFAULT_SCALE,
        label: str = "",
        margin: float = 0.05,
    ) -> PlotAxis:
        """Ticks-first construction; the range comes from scale.expand() over the tick positions."""
        return cls(range=scale.expand(ticks.positions, margin=margin), ticks=ticks, scale=scale, label=label)
