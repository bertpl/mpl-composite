"""Per-dimension bundle of the three transforms of one element's canvas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._transform import Transform


@dataclass(frozen=True)
class XYZTransform:
    """The three per-dimension (x, y, z) transforms of one element's canvas."""

    x: Transform
    y: Transform
    z: Transform
