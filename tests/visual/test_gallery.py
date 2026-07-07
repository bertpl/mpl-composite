"""Exact-compare every gallery figure against its committed baseline."""

from __future__ import annotations

import numpy as np
import pytest

from .gallery import GALLERY
from .regression import baseline_freetype, load_baseline, render_pixels, running_freetype

# Exact comparison is only meaningful when text rasterizes identically, i.e. on
# the FreeType version the baselines were rendered with (matplotlib wheels
# bundle their own FreeType, so this is a matplotlib-version property, not a
# platform property). Other legs still run the full functional suite.
pytestmark = pytest.mark.skipif(
    running_freetype() != baseline_freetype(),
    reason=(
        f"bundled FreeType {running_freetype()} != baseline FreeType {baseline_freetype()}; "
        "exact pixel comparison is only meaningful on the canonical rendering environment"
    ),
)


@pytest.mark.parametrize("name", sorted(GALLERY))
def test_gallery_figure_matches_baseline(name: str) -> None:
    # --- arrange ----------------------
    baseline = load_baseline(name)

    # --- act --------------------------
    rendered = render_pixels(GALLERY[name]())

    # --- assert -----------------------
    assert rendered.shape == baseline.shape
    assert np.array_equal(rendered, baseline), (
        f"gallery figure '{name}' drifted from its baseline; if the change is intended, "
        "regenerate via `make baselines` and eyeball the new image before committing"
    )
