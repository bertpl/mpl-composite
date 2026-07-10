"""Piecewise-linear color interpolation."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

RGB = tuple[float, float, float]


@dataclass(frozen=True)
class ColorRange:
    """Piecewise-linear interpolation over RGB color stops.

    Values below the first stop clamp to its color; values above the last stop
    clamp to its color.
    """

    stops: tuple[tuple[float, RGB], ...]

    def __post_init__(self) -> None:
        """Validate stop count and strictly increasing stop positions."""
        if len(self.stops) < 2:
            raise ValueError(f"ColorRange requires at least 2 stops (here: {len(self.stops)}).")
        positions = [position for position, _ in self.stops]
        if any(p1 >= p2 for p1, p2 in pairwise(positions)):
            raise ValueError(f"ColorRange stop positions must be strictly increasing (here: {positions}).")

    # --------------------------------------------------------------------------
    #  Interpolation
    # --------------------------------------------------------------------------
    def at(self, v: float) -> RGB:
        """Interpolated color at value v (clamped to the outer stops)."""
        if v <= self.stops[0][0]:
            return self.stops[0][1]
        if v >= self.stops[-1][0]:
            return self.stops[-1][1]

        for (p_lo, c_lo), (p_hi, c_hi) in pairwise(self.stops):
            if p_lo <= v <= p_hi:
                f = (v - p_lo) / (p_hi - p_lo)
                return (
                    c_lo[0] + f * (c_hi[0] - c_lo[0]),
                    c_lo[1] + f * (c_hi[1] - c_lo[1]),
                    c_lo[2] + f * (c_hi[2] - c_lo[2]),
                )
        raise AssertionError("unreachable: v lies between the outer stops")  # pragma: no cover

    # --------------------------------------------------------------------------
    #  Factory methods
    # --------------------------------------------------------------------------
    @classmethod
    def two_point(cls, v_min: float, color_min: RGB, v_max: float, color_max: RGB) -> ColorRange:
        """Construct the simplest ColorRange: one linear segment between two stops."""
        return cls(stops=((v_min, color_min), (v_max, color_max)))
