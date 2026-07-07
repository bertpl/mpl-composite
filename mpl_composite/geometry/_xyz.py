"""Per-dimension (x, y, z) bundles of scalars and ranges."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._range import Range


@dataclass(frozen=True)
class XYZ:
    """A per-dimension (x, y, z) triple of scalars — used for element sizes."""

    x: float
    y: float
    z: float


@dataclass(frozen=True)
class XYZRange:
    """A per-dimension (x, y, z) triple of Ranges — a rectangular block."""

    x: Range
    y: Range
    z: Range

    @property
    def size(self) -> XYZ:
        """Per-dimension extents."""
        return XYZ(self.x.size, self.y.size, self.z.size)

    def contains(self, other: XYZRange, *, tol: float = 1e-9) -> bool:
        """Check per-dimension containment of another block (see Range.contains for tolerance semantics)."""
        return (
            self.x.contains(other.x, tol=tol)
            and self.y.contains(other.y, tol=tol)
            and self.z.contains(other.z, tol=tol)
        )
