"""The immutable result of placing an element."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mpl_composite.canvas import Canvas


@dataclass(frozen=True)
class Layout:
    """The result of placing one element: its canvas plus its children's layouts.

    `children` is ordered identically to the element's child list, so draw()
    can zip them back together.
    """

    canvas: Canvas
    children: tuple[Layout, ...] = field(default=())
