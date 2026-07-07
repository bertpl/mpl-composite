from unittest.mock import Mock

import pytest

from mpl_composite.style import LineStyle


# ==================================================================================================
#  modify()
# ==================================================================================================
def test_modify_returns_new_instance_with_overrides() -> None:
    # --- arrange ----------------------
    ls = LineStyle(color=(1.0, 0.0, 0.0), width=2.0)

    # --- act --------------------------
    modified = ls.modify(width=3.0, zorder=5.0)

    # --- assert -----------------------
    assert modified == LineStyle(color=(1.0, 0.0, 0.0), width=3.0, zorder=5.0)
    assert ls.width == 2.0  # original untouched


def test_modify_rejects_unknown_field() -> None:
    # --- act / assert -----------------
    with pytest.raises(TypeError):
        LineStyle().modify(nope=1.0)


# ==================================================================================================
#  plot()
# ==================================================================================================
def test_plot_passes_line_and_marker_kwargs() -> None:
    # --- arrange ----------------------
    ax = Mock()
    ls = LineStyle(color=(0.0, 0.5, 1.0), width=2.0, style="--", marker="o", marker_size=3.0, zorder=7.0)

    # --- act --------------------------
    ls.plot(ax, [0.0, 1.0], [2.0, 3.0])

    # --- assert -----------------------
    ax.plot.assert_called_once()
    args, kwargs = ax.plot.call_args
    assert args == ([0.0, 1.0], [2.0, 3.0])
    assert kwargs["color"] == (0.0, 0.5, 1.0)
    assert kwargs["linewidth"] == 2.0
    assert kwargs["linestyle"] == "--"
    assert kwargs["marker"] == "o"
    assert kwargs["markersize"] == 3.0
    assert kwargs["zorder"] == 7.0


@pytest.mark.parametrize(
    "x, y, expected_x, expected_y",
    [
        (0.5, [1.0, 2.0, 3.0], [0.5, 0.5, 0.5], [1.0, 2.0, 3.0]),  # scalar x broadcast
        ([1.0, 2.0, 3.0], 0.5, [1.0, 2.0, 3.0], [0.5, 0.5, 0.5]),  # scalar y broadcast
        ([1.0], [1.0, 2.0], [1.0, 1.0], [1.0, 2.0]),  # single-element list broadcast
    ],
)
def test_plot_broadcasts_scalars(x: object, y: object, expected_x: list, expected_y: list) -> None:
    # --- arrange ----------------------
    ax = Mock()

    # --- act --------------------------
    LineStyle().plot(ax, x, y)

    # --- assert -----------------------
    args, _ = ax.plot.call_args
    assert args == (expected_x, expected_y)


def test_plot_rejects_incompatible_lengths() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="equal length"):
        LineStyle().plot(Mock(), [1.0, 2.0], [1.0, 2.0, 3.0])


def test_plot_with_line_disabled_uses_zero_linewidth() -> None:
    # --- arrange ----------------------
    ax = Mock()

    # --- act --------------------------
    LineStyle(line_enabled=False, marker="o").plot(ax, [0.0, 1.0], [0.0, 1.0])

    # --- assert -----------------------
    _, kwargs = ax.plot.call_args
    assert kwargs["linewidth"] == 0.0
    assert "color" not in kwargs  # line kwargs suppressed entirely
    assert kwargs["marker"] == "o"  # marker kwargs still apply


def test_marker_alpha_folded_into_rgba_color() -> None:
    # --- arrange ----------------------
    ax = Mock()

    # --- act --------------------------
    LineStyle(color=(1.0, 0.0, 0.0), alpha=0.5, marker="s").plot(ax, [0.0], [0.0])

    # --- assert -----------------------
    _, kwargs = ax.plot.call_args
    assert kwargs["markerfacecolor"] == (1.0, 0.0, 0.0, 0.5)
    assert kwargs["markeredgecolor"] == (1.0, 0.0, 0.0, 0.5)


def test_unfilled_marker_uses_white_face() -> None:
    # --- arrange ----------------------
    ax = Mock()

    # --- act --------------------------
    LineStyle(color=(1.0, 0.0, 0.0), marker_filled=False, marker="s").plot(ax, [0.0], [0.0])

    # --- assert -----------------------
    _, kwargs = ax.plot.call_args
    assert kwargs["markerfacecolor"] == (1.0, 1.0, 1.0, 1.0)
    assert kwargs["markeredgecolor"] == (1.0, 0.0, 0.0)


# ==================================================================================================
#  plot_sample()
# ==================================================================================================
def test_plot_sample_draws_segment_plus_centered_marker() -> None:
    # --- arrange ----------------------
    ax = Mock()

    # --- act --------------------------
    LineStyle(marker="o").plot_sample(ax, x_min=0.0, x_max=2.0, y=5.0)

    # --- assert -----------------------
    assert ax.plot.call_count == 2
    line_args, _ = ax.plot.call_args_list[0]
    marker_args, _ = ax.plot.call_args_list[1]
    assert line_args == ([0.0, 2.0], [5.0, 5.0])
    assert marker_args == (1.0, 5.0)  # marker at the segment center
