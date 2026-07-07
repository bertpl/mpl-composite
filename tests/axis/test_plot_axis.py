import dataclasses

import pytest

from mpl_composite.axis import PlotAxis, ScaleLog, Ticks, linear_ticks
from mpl_composite.geometry import Range
from mpl_composite.transforms import TransformLinear, TransformLog


# ==================================================================================================
#  Construction
# ==================================================================================================
def test_from_range_with_auto_ticks() -> None:
    # --- act --------------------------
    axis = PlotAxis.from_range(0.0, 10.0, label="time [s]")

    # --- assert -----------------------
    assert axis.range == Range(0.0, 10.0)
    assert axis.ticks == linear_ticks(0.0, 10.0)
    assert axis.label == "time [s]"


def test_from_range_without_auto_ticks() -> None:
    # --- act --------------------------
    axis = PlotAxis.from_range(0.0, 10.0, auto_ticks=False)

    # --- assert -----------------------
    assert axis.ticks.major == ()
    assert axis.ticks.minor == ()


def test_from_ticks_expands_range_over_positions() -> None:
    # --- arrange ----------------------
    ticks = Ticks.from_values(major=[0.0, 5.0, 10.0])

    # --- act --------------------------
    axis = PlotAxis.from_ticks(ticks, margin=0.1)

    # --- assert -----------------------
    assert axis.range.min == pytest.approx(-1.0)
    assert axis.range.max == pytest.approx(11.0)
    assert axis.ticks is ticks


def test_from_ticks_with_log_scale() -> None:
    # --- arrange ----------------------
    ticks = Ticks.from_values(major=[1.0, 10.0, 100.0])

    # --- act --------------------------
    axis = PlotAxis.from_ticks(ticks, scale=ScaleLog())

    # --- assert -----------------------
    assert axis.range.min == pytest.approx(10.0**-0.1)
    assert axis.range.max == pytest.approx(10.0**2.1)


# ==================================================================================================
#  Behavior
# ==================================================================================================
def test_transform_binds_without_mutating_the_axis() -> None:
    # --- arrange ----------------------
    axis = PlotAxis.from_range(0.0, 10.0)

    # --- act --------------------------
    t1 = axis.transform(Range(0.0, 1.0))
    t2 = axis.transform(Range(5.0, 7.0), reverse=True)

    # --- assert -----------------------
    assert isinstance(t1, TransformLinear)
    assert t1(10.0) == pytest.approx(1.0)
    assert t2(10.0) == pytest.approx(5.0)  # independent, reversed binding
    assert t1(10.0) == pytest.approx(1.0)  # first binding unaffected


def test_transform_dispatches_to_the_scale() -> None:
    # --- arrange ----------------------
    axis = PlotAxis.from_range(1.0, 100.0, scale=ScaleLog())

    # --- act / assert -----------------
    assert isinstance(axis.transform(Range(0.0, 1.0)), TransformLog)


def test_mid_point() -> None:
    # --- act / assert -----------------
    assert PlotAxis.from_range(0.0, 10.0).mid_point == pytest.approx(5.0)
    assert PlotAxis.from_range(1.0, 100.0, scale=ScaleLog()).mid_point == pytest.approx(10.0)


def test_plot_axis_is_immutable() -> None:
    # --- arrange ----------------------
    axis = PlotAxis.from_range(0.0, 10.0)

    # --- act / assert -----------------
    with pytest.raises(dataclasses.FrozenInstanceError):
        axis.label = "nope"
