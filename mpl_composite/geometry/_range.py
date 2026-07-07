"""1-D closed interval, the base primitive of all layout geometry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Range:
    """A closed 1-D interval [min, max] with min <= max."""

    min: float
    max: float

    def __post_init__(self) -> None:
        """Validate the interval ordering."""
        if self.min > self.max:
            raise ValueError(f"Range requires min <= max (here: min={self.min}, max={self.max}).")

    # --------------------------------------------------------------------------
    #  Derived properties
    # --------------------------------------------------------------------------
    @property
    def size(self) -> float:
        """Extent of the interval (max - min)."""
        return self.max - self.min

    @property
    def center(self) -> float:
        """Midpoint of the interval."""
        return 0.5 * (self.min + self.max)

    # --------------------------------------------------------------------------
    #  Queries
    # --------------------------------------------------------------------------
    def contains(self, other: float | Range, *, tol: float = 1e-9) -> bool:
        """Check containment of a value or a whole Range, with tolerance.

        The tolerance is symmetric and combines absolute and relative parts
        (`tol * max(1, |min|, |max|)`), so it behaves identically for
        negative, zero-crossing, and large intervals.

        Args:
            other: A value or Range to test for containment.
            tol: Relative/absolute tolerance factor.
        """
        eps = tol * max(1.0, abs(self.min), abs(self.max))
        if isinstance(other, Range):
            return (self.min - eps <= other.min) and (other.max <= self.max + eps)
        return self.min - eps <= other <= self.max + eps

    def at(self, p: float) -> float:
        """Interpolate within the interval: at(0.0) == min, at(1.0) == max."""
        return self.min + p * self.size
