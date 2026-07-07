from unittest.mock import Mock

from mpl_composite.axis import PlotAxis, ScaleLog, Ticks
from mpl_composite.canvas import Region
from mpl_composite.geometry import XYZ, Range, XYZRange
from mpl_composite.plot._axis_bars import _XAxisBar, _YAxisBar, bar_thickness
from mpl_composite.style import DEFAULT_THEME

_TICKS = Ticks(major=(0.0, 5.0, 10.0), major_labels=("0", "5", "10"), minor=(2.5, 7.5), minor_labels=("", "7.5"))
_AXIS = PlotAxis(range=Range(0.0, 10.0), ticks=_TICKS, label="value")
_LOG_AXIS = PlotAxis.from_range(1.0, 1000.0, scale=ScaleLog())


def _region(ax) -> Region:
    return Region(ax=ax, xyz=XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 1.0)))


# ==================================================================================================
#  bar_thickness
# ==================================================================================================
def test_bar_thickness_grows_when_labeled() -> None:
    # --- act / assert -----------------
    assert bar_thickness(1.0, labeled=True) > bar_thickness(1.0, labeled=False) > 0.0


# ==================================================================================================
#  _XAxisBar
# ==================================================================================================
def test_x_bar_measures_declared_box() -> None:
    # --- act / assert -----------------
    assert _XAxisBar(_AXIS, 2.0, 0.3, DEFAULT_THEME).measure() == XYZ(2.0, 0.3, 0.0)


def test_x_bar_binds_x_to_the_axis_scale() -> None:
    # --- arrange ----------------------
    bar = _XAxisBar(_LOG_AXIS, 1.0, 0.2, DEFAULT_THEME)

    # --- act --------------------------
    layout = bar.place(_region(Mock()))

    # --- assert -----------------------
    assert layout.canvas.x == _LOG_AXIS.range
    assert not layout.canvas._trans.x.is_linear()
    assert layout.canvas._trans.y.is_linear()


def test_x_bar_draws_ticks_and_labels(fig_ax) -> None:
    # --- arrange ----------------------
    _fig, ax = fig_ax
    bar = _XAxisBar(_AXIS, 1.0, 0.2, DEFAULT_THEME)
    layout = bar.place(_region(ax))

    # --- act --------------------------
    bar.draw(layout)

    # --- assert -----------------------
    assert len(ax.lines) == len(_TICKS.major) + len(_TICKS.minor)
    texts = [t.get_text() for t in ax.texts]
    assert texts == ["0", "5", "10", "7.5", "value"]  # majors, non-empty minors, axis label


def test_x_bar_without_label_draws_no_label_text(fig_ax) -> None:
    # --- arrange ----------------------
    _fig, ax = fig_ax
    axis = PlotAxis(range=Range(0.0, 10.0), ticks=_TICKS)
    bar = _XAxisBar(axis, 1.0, 0.2, DEFAULT_THEME)
    layout = bar.place(_region(ax))

    # --- act --------------------------
    bar.draw(layout)

    # --- assert -----------------------
    assert "value" not in [t.get_text() for t in ax.texts]


# ==================================================================================================
#  _YAxisBar
# ==================================================================================================
def test_y_bar_measures_declared_box() -> None:
    # --- act / assert -----------------
    assert _YAxisBar(_AXIS, 0.3, 2.0, DEFAULT_THEME).measure() == XYZ(0.3, 2.0, 0.0)


def test_y_bar_binds_y_to_the_axis_scale() -> None:
    # --- arrange ----------------------
    bar = _YAxisBar(_LOG_AXIS, 0.2, 1.0, DEFAULT_THEME)

    # --- act --------------------------
    layout = bar.place(_region(Mock()))

    # --- assert -----------------------
    assert layout.canvas.y == _LOG_AXIS.range
    assert not layout.canvas._trans.y.is_linear()
    assert layout.canvas._trans.x.is_linear()


def test_y_bar_draws_ticks_and_rotated_label(fig_ax) -> None:
    # --- arrange ----------------------
    _fig, ax = fig_ax
    bar = _YAxisBar(_AXIS, 0.2, 1.0, DEFAULT_THEME)
    layout = bar.place(_region(ax))

    # --- act --------------------------
    bar.draw(layout)

    # --- assert -----------------------
    assert len(ax.lines) == len(_TICKS.major) + len(_TICKS.minor)
    label_artist = next(t for t in ax.texts if t.get_text() == "value")
    assert label_artist.get_rotation() == 90.0
