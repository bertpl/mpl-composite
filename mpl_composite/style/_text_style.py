"""Text rendering style value objects."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import StrEnum


class FontWeight(StrEnum):
    """Font weight; values are the matplotlib fontweight strings."""

    LIGHT = "light"
    NORMAL = "normal"
    SEMI_BOLD = "semibold"
    BOLD = "bold"
    BLACK = "black"


@dataclass(frozen=True)
class TextStyle:
    """Text rendering style (position and alignment are drawing-call arguments, not style)."""

    size: float = 10.0
    weight: FontWeight = FontWeight.NORMAL
    color: str | tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_deg: float = 0.0

    def modify(self, **overrides: object) -> TextStyle:
        """Copy with the given fields replaced (dataclasses.replace semantics)."""
        return dataclasses.replace(self, **overrides)  # type: ignore[arg-type]
