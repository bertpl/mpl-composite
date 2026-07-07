import pytest

from mpl_composite import LineStyle
from mpl_composite.canvas import Region
from mpl_composite.geometry import Range, XYZRange
from mpl_composite.plot import Legend, LegendEntry

_STYLE = LineStyle(color=(0.2, 0.3, 0.8))
_ENTRIES = [LegendEntry("alpha", _STYLE), LegendEntry("beta", _STYLE), LegendEntry("gamma", _STYLE)]


def _region(ax) -> Region:
    return Region(ax=ax, xyz=XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 1.0)))


# ==================================================================================================
#  Construction & measurement
# ==================================================================================================
def test_rejects_empty_entries_and_bad_geometry() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="at least one"):
        Legend([])
    with pytest.raises(ValueError, match="n_cols"):
        Legend(_ENTRIES, n_cols=0)
    with pytest.raises(ValueError, match="row_height"):
        Legend(_ENTRIES, row_height=0.0)


def test_measure_scales_with_row_height() -> None:
    # --- act --------------------------
    small = Legend(_ENTRIES, row_height=0.05).measure()
    large = Legend(_ENTRIES, row_height=0.10).measure()

    # --- assert -----------------------
    assert large.y == pytest.approx(2 * small.y, rel=0.01)
    assert small.x < large.x < 2 * small.x  # text scales; the swatch width stays fixed


def test_more_columns_widen_and_flatten_the_legend() -> None:
    # --- act --------------------------
    one_col = Legend(_ENTRIES, n_cols=1).measure()
    two_cols = Legend(_ENTRIES, n_cols=2).measure()

    # --- assert -----------------------
    assert two_cols.x > one_col.x
    assert two_cols.y < one_col.y


def test_excess_columns_cap_at_the_entry_count() -> None:
    # --- act --------------------------
    capped = Legend(_ENTRIES, n_cols=10).measure()
    exact = Legend(_ENTRIES, n_cols=3).measure()

    # --- assert -----------------------
    assert capped == exact


def test_wider_labels_widen_the_legend() -> None:
    # --- arrange ----------------------
    short = Legend([LegendEntry("ab", _STYLE)])
    long = Legend([LegendEntry("a considerably longer label", _STYLE)])

    # --- act / assert -----------------
    assert long.measure().x > short.measure().x


# ==================================================================================================
#  Drawing
# ==================================================================================================
def test_draw_produces_frame_samples_and_labels(fig_ax) -> None:
    # --- arrange ----------------------
    _fig, ax = fig_ax
    legend = Legend(_ENTRIES, n_cols=2)
    layout = legend.place(_region(ax))

    # --- act --------------------------
    legend.draw(layout)

    # --- assert -----------------------
    assert len(ax.patches) == 1  # the framed background
    assert len(ax.lines) == 2 * len(_ENTRIES)  # sample segment + marker per entry
    assert [t.get_text() for t in ax.texts] == ["alpha", "beta", "gamma"]


def test_frameless_draw_has_no_background(fig_ax) -> None:
    # --- arrange ----------------------
    _fig, ax = fig_ax
    legend = Legend(_ENTRIES, frame=False)
    layout = legend.place(_region(ax))

    # --- act --------------------------
    legend.draw(layout)

    # --- assert -----------------------
    assert len(ax.patches) == 0
