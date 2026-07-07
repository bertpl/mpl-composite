"""Plain multi-format figure saving."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.figure import Figure


def save_figure(
    fig: Figure,
    path: Path | str,
    *,
    formats: Sequence[str] = ("png",),
    dpi: int = 300,
    transparent: bool = False,
) -> list[Path]:
    """Save one figure in each format next to `path` (suffix swapped per format).

    Args:
        fig: The figure to save.
        path: Target path; its suffix is replaced per format.
        formats: File formats (matplotlib savefig formats, e.g. png/pdf/svg).
        dpi: Raster resolution.
        transparent: Transparent background.

    Returns:
        The written paths, in `formats` order.
    """
    path = Path(path)
    written = []
    for fmt in formats:
        target = path.with_suffix(f".{fmt}")
        fig.savefig(target, dpi=dpi, transparent=transparent, bbox_inches="tight")
        written.append(target)
    return written
