"""Shared machinery for the visual-regression harness: rendering and baseline IO.

Comparison is exact (bit-identical pixels): Agg renders deterministically for a
given matplotlib + bundled-FreeType combination, and platform plays no role.
The only drift axis is the FreeType version bundled with the matplotlib wheel,
so baselines record it and the tests skip when the running version differs.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib

matplotlib.use("Agg", force=True)  # baselines and comparisons are Agg renders, everywhere

import matplotlib.image
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    import numpy as np

    from mpl_composite import CompositeFigure

BASELINE_DIR = Path(__file__).parent / "baselines"
ENVIRONMENT_FILE = BASELINE_DIR / "environment.json"
DPI = 100


def render_pixels(composite_figure: CompositeFigure) -> np.ndarray:
    """Render a composite figure to its PNG pixel array (via an in-memory savefig)."""
    fig = composite_figure.render()
    try:
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=DPI)
        buffer.seek(0)
        return matplotlib.image.imread(buffer, format="png")
    finally:
        plt.close(fig)


def load_baseline(name: str) -> np.ndarray:
    """Load a committed baseline's pixel array by gallery name."""
    return matplotlib.image.imread(BASELINE_DIR / f"{name}.png", format="png")


def running_freetype() -> str:
    """The FreeType version bundled with the running matplotlib."""
    return matplotlib.ft2font.__freetype_version__


def baseline_freetype() -> str:
    """The FreeType version the committed baselines were rendered with."""
    return str(json.loads(ENVIRONMENT_FILE.read_text())["freetype"])
