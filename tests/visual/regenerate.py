"""Regenerate the committed visual-regression baselines from the gallery.

Run via `make baselines`. Renders every gallery figure to
`tests/visual/baselines/` and records the rendering environment, which the
tests use to decide whether an exact comparison is meaningful.
"""

from __future__ import annotations

import json

import matplotlib
import matplotlib.pyplot as plt

from .gallery import GALLERY
from .regression import BASELINE_DIR, DPI, ENVIRONMENT_FILE


def main() -> None:
    """Render all gallery figures to the baseline directory and stamp environment.json."""
    BASELINE_DIR.mkdir(exist_ok=True)
    for name, build in GALLERY.items():
        fig = build().render()
        fig.savefig(BASELINE_DIR / f"{name}.png", dpi=DPI)
        plt.close(fig)
        print(f"rendered {name}.png")

    environment = {
        "freetype": matplotlib.ft2font.__freetype_version__,
        "matplotlib": matplotlib.__version__,
    }
    ENVIRONMENT_FILE.write_text(json.dumps(environment, indent=2) + "\n")
    print(f"recorded environment: {environment}")


if __name__ == "__main__":
    main()
