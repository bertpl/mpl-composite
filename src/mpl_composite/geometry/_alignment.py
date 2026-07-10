"""Alignment and margin primitives for fitting elements into layout cells."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ._range import Range


class HAlign(StrEnum):
    """Horizontal alignment of an extent inside a horizontal range."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    FILL = "fill"

    def fit(self, into: Range, size: float) -> Range:
        """Place an extent of `size` inside `into` per this alignment.

        LEFT anchors at into.min, RIGHT at into.max, CENTER centers; FILL
        returns `into` itself (ignoring `size`).
        """
        if self is HAlign.LEFT:
            return Range(into.min, into.min + size)
        if self is HAlign.RIGHT:
            return Range(into.max - size, into.max)
        if self is HAlign.CENTER:
            return Range(into.center - (0.5 * size), into.center + (0.5 * size))
        return into  # FILL


class VAlign(StrEnum):
    """Vertical alignment of an extent inside a vertical range."""

    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    FILL = "fill"

    def fit(self, into: Range, size: float, *, top_at_max: bool = True) -> Range:
        """Place an extent of `size` inside `into` per this alignment.

        CENTER centers; FILL returns `into` itself (ignoring `size`).

        Args:
            into: The vertical range to place the extent in.
            size: The extent to place.
            top_at_max: Orientation of `into`: True when larger values sit
                visually higher (axis coordinates, matplotlib's default),
                False in top-down spaces (composite plot coordinates, where
                row 0 sits at the range minimum).
        """
        if self is VAlign.FILL:
            return into
        if self is VAlign.CENTER:
            return Range(into.center - (0.5 * size), into.center + (0.5 * size))
        if (self is VAlign.TOP) == top_at_max:
            return Range(into.max - size, into.max)
        return Range(into.min, into.min + size)


@dataclass(frozen=True)
class Margin:
    """2-D whitespace around an element inside its layout cell (layout units).

    Margins are a 2-D concept only: z layering is managed by disjoint
    stacking and takes no margin.
    """

    left: float = 0.0
    right: float = 0.0
    top: float = 0.0
    bottom: float = 0.0

    @classmethod
    def uniform(cls, m: float) -> Margin:
        """Equal margin on all four sides."""
        return cls(left=m, right=m, top=m, bottom=m)

    @property
    def width(self) -> float:
        """Total horizontal margin (left + right)."""
        return self.left + self.right

    @property
    def height(self) -> float:
        """Total vertical margin (top + bottom)."""
        return self.top + self.bottom
