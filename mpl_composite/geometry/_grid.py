"""Ordered 1-D grid of keyed cells with cumulative ranges."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._range import Range

if TYPE_CHECKING:
    from collections.abc import Hashable, Iterable


class LinearGrid:
    """Ordered keys -> cell sizes, forming a 1-D grid of consecutive cells starting at 0.

    Used for table rows, table columns, composite rows/cols, and z-stacking.
    Construction is complete at __init__ time — every caller knows all cells up
    front, and immutability keeps element measurement side-effect-free.
    """

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(self, keys: Iterable[Hashable], sizes: Iterable[float]) -> None:
        """Build the grid from parallel keys and cell sizes.

        Args:
            keys: Unique, hashable cell keys, in cell order.
            sizes: Non-negative cell sizes, parallel to `keys`.

        Raises:
            ValueError: On a keys/sizes length mismatch, a duplicate key, or a
                negative size.
        """
        keys, sizes = list(keys), list(sizes)
        if len(keys) != len(sizes):
            raise ValueError(f"keys and sizes must have equal length (here: {len(keys)} vs {len(sizes)}).")
        if any(size < 0 for size in sizes):
            raise ValueError("cell sizes must be non-negative.")

        self._index_by_key = {key: i for i, key in enumerate(keys)}
        if len(self._index_by_key) != len(keys):
            raise ValueError("keys must be unique.")

        self._ranges: list[Range] = []
        position = 0.0
        for size in sizes:
            self._ranges.append(Range(position, position + size))
            position += size

    # --------------------------------------------------------------------------
    #  Cell access
    # --------------------------------------------------------------------------
    def __len__(self) -> int:
        """Number of cells."""
        return len(self._ranges)

    def __getitem__(self, key: Hashable) -> Range:
        """Cell range by key."""
        return self._ranges[self._index_by_key[key]]

    def range_by_index(self, index: int) -> Range:
        """Cell range by 0-based cell index."""
        return self._ranges[index]

    # --------------------------------------------------------------------------
    #  Grid-wide queries
    # --------------------------------------------------------------------------
    def boundaries(self, *, include_edges: bool = True) -> list[float]:
        """Cell boundary positions, in order; optionally without the two outer edges.

        An empty grid has no boundaries ([]).
        """
        if not self._ranges:
            return []
        if include_edges:
            return [r.min for r in self._ranges] + [self._ranges[-1].max]
        return [r.min for r in self._ranges[1:]]

    @property
    def span(self) -> Range:
        """Full extent: Range(0, total size); Range(0, 0) for an empty grid."""
        if not self._ranges:
            return Range(0.0, 0.0)
        return Range(0.0, self._ranges[-1].max)
