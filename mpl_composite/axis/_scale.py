"""Axis scale kinds as a small polymorphic hierarchy owning all scale-dependent behavior."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mpl_composite.geometry import Range
from mpl_composite.transforms import Transform

from ._ticks import Ticks, linear_ticks, log_ticks

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


# ==================================================================================================
#  Scale (base class)
# ==================================================================================================
class Scale(ABC):
    """An axis scale kind: owns every scale-dependent behavior of a data axis.

    A dataclass hierarchy rather than an enum because scales carry parameters
    (log base, lin-log split point); adding a scale never touches PlotAxis.
    """

    @abstractmethod
    def transform(self, value_range: Range, ax_range: Range, *, reverse: bool = False) -> Transform:
        """Build the plot->axis Transform of this scale kind."""

    @abstractmethod
    def ticks(self, value_range: Range, *, n_major_target: int = 5, fmt: Callable[[float], str] | None = None) -> Ticks:
        """Generate ticks for a value range via the matching raw algorithm(s)."""

    @abstractmethod
    def expand(self, values: Sequence[float], *, margin: float = 0.05) -> Range:
        """Auto-range around values, with the relative margin taken in this scale's space."""

    def mid_point(self, value_range: Range) -> float:
        """Visual center of a value range in data values (e.g. geometric mean for log).

        Derived from the scale's own transform (the value mapping to the middle
        of the screen extent), so every scale gets it for free.
        """
        result = self.transform(value_range, Range(0.0, 1.0)).inv(0.5)
        assert isinstance(result, float)  # noqa: S101  (scalar in -> scalar out, by Transform contract)
        return result


# ==================================================================================================
#  ScaleLinear
# ==================================================================================================
@dataclass(frozen=True)
class ScaleLinear(Scale):
    """Plain linear scale."""

    n_minor_per_major: int = 4

    def transform(self, value_range: Range, ax_range: Range, *, reverse: bool = False) -> Transform:
        """Build a linear Transform."""
        return Transform.linear(value_range, ax_range, reverse)

    def ticks(self, value_range: Range, *, n_major_target: int = 5, fmt: Callable[[float], str] | None = None) -> Ticks:
        """Generate nice-step linear ticks."""
        return linear_ticks(
            value_range.min,
            value_range.max,
            n_major_target=n_major_target,
            n_minor_per_major=self.n_minor_per_major,
            fmt=fmt,
        )

    def expand(self, values: Sequence[float], *, margin: float = 0.05) -> Range:
        """Pad the value extremes with `margin` times the span on each side.

        A degenerate extreme (all values equal) is padded by
        `margin * max(1, |value|)` instead.
        """
        lo, hi = min(values), max(values)
        pad = margin * (hi - lo) if hi > lo else margin * max(1.0, abs(lo))
        return Range(lo - pad, hi + pad)


# ==================================================================================================
#  ScaleLog
# ==================================================================================================
@dataclass(frozen=True)
class ScaleLog(Scale):
    """Logarithmic scale."""

    base: float = 10.0
    minor_subs: tuple[float, ...] = (2.0, 5.0)

    def transform(self, value_range: Range, ax_range: Range, *, reverse: bool = False) -> Transform:
        """Build a logarithmic Transform."""
        return Transform.log(value_range, ax_range, reverse)

    def ticks(self, value_range: Range, *, n_major_target: int = 5, fmt: Callable[[float], str] | None = None) -> Ticks:
        """Generate base-power log ticks (n_major_target is ignored: the decades decide)."""
        return log_ticks(value_range.min, value_range.max, base=self.base, minor_subs=self.minor_subs, fmt=fmt)

    def expand(self, values: Sequence[float], *, margin: float = 0.05) -> Range:
        """Pad the value extremes with `margin` times the log-space span on each side.

        A degenerate extreme (all values equal) is padded by a factor
        `base**margin` instead.

        Raises:
            ValueError: If any value is non-positive.
        """
        lo, hi = min(values), max(values)
        if lo <= 0:
            raise ValueError(f"ScaleLog.expand requires strictly positive values (here: min={lo}).")
        log_lo, log_hi = math.log(lo), math.log(hi)
        pad = margin * (log_hi - log_lo) if hi > lo else margin * math.log(self.base)
        return Range(math.exp(log_lo - pad), math.exp(log_hi + pad))


# ==================================================================================================
#  ScaleLinLog
# ==================================================================================================
@dataclass(frozen=True)
class ScaleLinLog(Scale):
    """Linear below lin_max, logarithmic above — for axes that must show 0 (or
    negative values) and still span decades.
    """

    lin_max: float
    lin_fraction: float

    def transform(self, value_range: Range, ax_range: Range, *, reverse: bool = False) -> Transform:
        """Build a lin-log Transform (requires value_range to straddle lin_max)."""
        return Transform.lin_log(value_range, ax_range, plot_lin_max=self.lin_max, ax_lin_fraction=self.lin_fraction, reverse=reverse)

    def ticks(self, value_range: Range, *, n_major_target: int = 5, fmt: Callable[[float], str] | None = None) -> Ticks:
        """Tick composition across the lin-log seam is not implemented yet.

        Raises:
            NotImplementedError: Always — supply hand-made Ticks (e.g. via
                Ticks.from_values) for lin-log axes for now.
        """
        raise NotImplementedError("ScaleLinLog.ticks is not implemented yet; supply hand-made Ticks instead.")

    def expand(self, values: Sequence[float], *, margin: float = 0.05) -> Range:
        """Pad each value extreme in its own segment's space.

        The lower extreme is padded linearly when it sits below lin_max and
        logarithmically otherwise; the upper extreme vice versa. A degenerate
        extreme (all values equal) is padded per ScaleLinear.expand semantics.
        """
        lo, hi = min(values), max(values)
        if hi == lo:
            pad = margin * max(1.0, abs(lo))
            return Range(lo - pad, hi + pad)

        # --- lower edge -----------------------------------
        if lo < self.lin_max:
            new_lo = lo - margin * (min(hi, self.lin_max) - lo)
        else:
            new_lo = math.exp(math.log(lo) - margin * (math.log(hi) - math.log(lo)))

        # --- upper edge -----------------------------------
        if hi > self.lin_max:
            new_hi = math.exp(math.log(hi) + margin * (math.log(hi) - math.log(max(lo, self.lin_max))))
        else:
            new_hi = hi + margin * (hi - lo)

        return Range(new_lo, new_hi)
