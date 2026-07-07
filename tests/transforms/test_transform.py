import numpy as np
import pytest

from mpl_composite.geometry import Range
from mpl_composite.transforms import Transform, TransformLinear, TransformLinLog, TransformLog


# ==================================================================================================
#  TransformLinear
# ==================================================================================================
@pytest.mark.parametrize(
    "v_plot, v_ax",
    [
        (0.0, 10.0),
        (1.0, 20.0),
        (0.5, 15.0),
        (-1.0, 0.0),  # extrapolation below the range
        (2.0, 30.0),  # extrapolation above the range
    ],
)
def test_linear_forward_backward(v_plot: float, v_ax: float) -> None:
    # --- arrange ----------------------
    t = Transform.linear(Range(0.0, 1.0), Range(10.0, 20.0))

    # --- act / assert -----------------
    assert t(v_plot) == pytest.approx(v_ax)
    assert t.inv(v_ax) == pytest.approx(v_plot)


@pytest.mark.parametrize(
    "v_plot, v_ax",
    [
        (0.0, 20.0),  # plot min maps to axis max
        (1.0, 10.0),  # plot max maps to axis min
        (0.25, 17.5),
    ],
)
def test_linear_reversed(v_plot: float, v_ax: float) -> None:
    # --- arrange ----------------------
    t = Transform.linear(Range(0.0, 1.0), Range(10.0, 20.0), reverse=True)

    # --- act / assert -----------------
    assert t(v_plot) == pytest.approx(v_ax)
    assert t.inv(v_ax) == pytest.approx(v_plot)


def test_linear_is_linear() -> None:
    # --- act / assert -----------------
    assert Transform.linear(Range(0.0, 1.0), Range(0.0, 1.0)).is_linear()


@pytest.mark.parametrize("reverse", [False, True])
def test_linear_degenerate_plot_range(reverse: bool) -> None:
    # --- arrange ----------------------
    t = Transform.linear(Range(2.0, 2.0), Range(10.0, 20.0), reverse=reverse)

    # --- act / assert -----------------
    assert t(2.0) == pytest.approx(15.0)  # everything maps to the axis center
    assert t.inv(12.0) == pytest.approx(2.0)  # inverse returns the plot center


def test_linear_degenerate_ax_range() -> None:
    # --- arrange ----------------------
    t = Transform.linear(Range(0.0, 1.0), Range(5.0, 5.0))

    # --- act / assert -----------------
    assert t(0.7) == pytest.approx(5.0)
    assert t.inv(5.0) == pytest.approx(0.5)  # inverse degenerates to the plot center


# ==================================================================================================
#  TransformLog
# ==================================================================================================
@pytest.mark.parametrize(
    "v_plot, v_ax",
    [
        (1.0, 0.0),
        (100.0, 1.0),
        (10.0, 0.5),  # geometric center maps to axis center
    ],
)
def test_log_forward_backward(v_plot: float, v_ax: float) -> None:
    # --- arrange ----------------------
    t = Transform.log(Range(1.0, 100.0), Range(0.0, 1.0))

    # --- act / assert -----------------
    assert t(v_plot) == pytest.approx(v_ax)
    assert t.inv(v_ax) == pytest.approx(v_plot)


def test_log_reversed_round_trip() -> None:
    # --- arrange ----------------------
    t = Transform.log(Range(1.0, 1000.0), Range(0.0, 3.0), reverse=True)

    # --- act --------------------------
    values = [1.0, 5.0, 50.0, 999.0]
    round_tripped = t.inv(t(values))

    # --- assert -----------------------
    assert t(1.0) == pytest.approx(3.0)  # plot min maps to axis max
    assert t(1000.0) == pytest.approx(0.0)
    assert round_tripped == pytest.approx(values)


def test_log_rejects_non_positive_range() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="strictly positive"):
        Transform.log(Range(0.0, 10.0), Range(0.0, 1.0))


def test_log_is_not_linear() -> None:
    # --- act / assert -----------------
    assert not Transform.log(Range(1.0, 10.0), Range(0.0, 1.0)).is_linear()


def test_log_degenerate_plot_range() -> None:
    # --- arrange ----------------------
    t = Transform.log(Range(5.0, 5.0), Range(0.0, 1.0))

    # --- act / assert -----------------
    assert t(5.0) == pytest.approx(0.5)


# ==================================================================================================
#  TransformLinLog
# ==================================================================================================
def _linlog() -> TransformLinLog:
    # [0, 1] linear onto [0, 0.25]; [1, 1000] log onto [0.25, 1.0]
    return Transform.lin_log(Range(0.0, 1000.0), Range(0.0, 1.0), plot_lin_max=1.0, ax_lin_fraction=0.25)


@pytest.mark.parametrize(
    "v_plot, v_ax",
    [
        (0.0, 0.0),
        (0.5, 0.125),  # linear part
        (1.0, 0.25),  # the seam
        (10.0, 0.5),  # log part: one decade of three
        (1000.0, 1.0),
    ],
)
def test_linlog_forward_backward(v_plot: float, v_ax: float) -> None:
    # --- arrange ----------------------
    t = _linlog()

    # --- act / assert -----------------
    assert t(v_plot) == pytest.approx(v_ax)
    assert t.inv(v_ax) == pytest.approx(v_plot)


def test_linlog_is_continuous_at_the_seam() -> None:
    # --- arrange ----------------------
    t = _linlog()

    # --- act / assert -----------------
    assert t(1.0 - 1e-12) == pytest.approx(t(1.0 + 1e-12), abs=1e-9)


def test_linlog_reversed_round_trip() -> None:
    # --- arrange ----------------------
    t = Transform.lin_log(Range(0.0, 100.0), Range(0.0, 1.0), plot_lin_max=1.0, ax_lin_fraction=0.5, reverse=True)

    # --- act --------------------------
    values = [0.0, 0.5, 1.0, 10.0, 100.0]
    round_tripped = t.inv(t(values))

    # --- assert -----------------------
    assert t(0.0) == pytest.approx(1.0)  # plot min maps to axis max
    assert t(100.0) == pytest.approx(0.0)
    assert round_tripped == pytest.approx(values)


@pytest.mark.parametrize(
    "plot_lin_max, ax_lin_fraction, match",
    [
        (0.0, 0.5, "strictly inside"),  # on the range edge
        (1000.0, 0.5, "strictly inside"),
        (-1.0, 0.5, "strictly inside"),
        (1.0, 0.0, r"\(0, 1\)"),
        (1.0, 1.0, r"\(0, 1\)"),
    ],
)
def test_linlog_rejects_invalid_parameters(plot_lin_max: float, ax_lin_fraction: float, match: str) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match=match):
        Transform.lin_log(Range(0.0, 1000.0), Range(0.0, 1.0), plot_lin_max=plot_lin_max, ax_lin_fraction=ax_lin_fraction)


def test_linlog_rejects_non_positive_seam() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="strictly positive"):
        Transform.lin_log(Range(-10.0, 1000.0), Range(0.0, 1.0), plot_lin_max=-1.0, ax_lin_fraction=0.5)


def test_linlog_is_not_linear() -> None:
    # --- act / assert -----------------
    assert not _linlog().is_linear()


# ==================================================================================================
#  Shared behavior: type preservation & map_range
# ==================================================================================================
def test_type_preservation() -> None:
    # --- arrange ----------------------
    t = Transform.linear(Range(0.0, 1.0), Range(0.0, 10.0))

    # --- act --------------------------
    as_scalar = t(0.5)
    as_list = t([0.0, 0.5, 1.0])
    as_array = t(np.array([0.0, 0.5, 1.0]))

    # --- assert -----------------------
    assert isinstance(as_scalar, float)
    assert isinstance(as_list, list)
    assert isinstance(as_array, np.ndarray)
    assert as_list == pytest.approx([0.0, 5.0, 10.0])
    assert as_array == pytest.approx(np.array([0.0, 5.0, 10.0]))


def test_inv_type_preservation() -> None:
    # --- arrange ----------------------
    t = Transform.linear(Range(0.0, 1.0), Range(0.0, 10.0))

    # --- act / assert -----------------
    assert isinstance(t.inv(5.0), float)
    assert isinstance(t.inv([0.0, 5.0]), list)
    assert isinstance(t.inv(np.array([0.0, 5.0])), np.ndarray)


@pytest.mark.parametrize(
    "t, r, expected",
    [
        (TransformLinear(Range(0.0, 1.0), Range(0.0, 10.0)), Range(0.2, 0.4), Range(2.0, 4.0)),
        # reversed: mapped endpoints swap, map_range keeps min <= max
        (TransformLinear(Range(0.0, 1.0), Range(0.0, 10.0), reverse=True), Range(0.2, 0.4), Range(6.0, 8.0)),
        (TransformLog(Range(1.0, 100.0), Range(0.0, 2.0)), Range(1.0, 10.0), Range(0.0, 1.0)),
    ],
)
def test_map_range(t: Transform, r: Range, expected: Range) -> None:
    # --- act --------------------------
    mapped = t.map_range(r)

    # --- assert -----------------------
    assert mapped.min == pytest.approx(expected.min)
    assert mapped.max == pytest.approx(expected.max)


def test_properties_expose_construction_arguments() -> None:
    # --- arrange ----------------------
    t = Transform.linear(Range(0.0, 1.0), Range(10.0, 20.0), reverse=True)

    # --- act / assert -----------------
    assert t.plot_range == Range(0.0, 1.0)
    assert t.ax_range == Range(10.0, 20.0)
    assert t.is_reverse
