"""The gallery of figures pinned by visual-regression baselines.

Every entry renders through the full measure -> place -> draw lifecycle; new
element families add a figure here so their visual output gets pinned.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mpl_composite import Composite, CompositeFigure, Spacer, Text

if TYPE_CHECKING:
    from collections.abc import Callable


def demo_composite() -> CompositeFigure:
    """Title over a 2x2 inner grid with spacers: the v0.1.0 engine smoke figure."""
    fig = CompositeFigure(fig_inch_per_unit=4.0)
    fig.add(0, 0, Text(1.0, 0.15, "Demo title"))
    inner = Composite()
    inner.add(0, 0, Text(0.4, 0.1, "top left"))
    inner.add(0, 1, Spacer(0.1, 0.1))
    inner.add(1, 0, Spacer(0.1, 0.1))
    inner.add(1, 1, Text(0.4, 0.1, "bottom right"))
    fig.add(1, 0, inner, margin=0.05)
    return fig


GALLERY: dict[str, Callable[[], CompositeFigure]] = {
    "demo_composite": demo_composite,
}
