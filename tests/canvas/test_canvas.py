from unittest.mock import Mock

import pytest

from mpl_composite.canvas import Canvas, LayoutError, Region
from mpl_composite.geometry import HAlign, Range, VAlign, XYZRange
from mpl_composite.style import LineStyle, TextStyle
from mpl_composite.transforms import Transform, XYZTransform


def _canvas(ax=None, *, y_reverse: bool = False, x_log: bool = False) -> Canvas:
    """Canvas over plot ranges x=[0,10], y=[0,5], z=[0,1] mapped to ax ranges x/y=[0,1], z=[10,20]."""
    x_ax, y_ax, z_ax = Range(0.0, 1.0), Range(0.0, 1.0), Range(10.0, 20.0)
    region = Region(ax=ax if ax is not None else Mock(), xyz=XYZRange(x=x_ax, y=y_ax, z=z_ax))
    x_plot = Range(1.0, 10.0) if x_log else Range(0.0, 10.0)
    return Canvas(
        region,
        XYZTransform(
            x=Transform.log(x_plot, x_ax) if x_log else Transform.linear(x_plot, x_ax),
            y=Transform.linear(Range(0.0, 5.0), y_ax, reverse=y_reverse),
            z=Transform.linear(Range(0.0, 1.0), z_ax),
        ),
    )


# ==================================================================================================
#  Coordinate info
# ==================================================================================================
def test_plot_coordinate_ranges() -> None:
    # --- arrange ----------------------
    canvas = _canvas()

    # --- act / assert -----------------
    assert canvas.x == Range(0.0, 10.0)
    assert canvas.y == Range(0.0, 5.0)
    assert canvas.z == Range(0.0, 1.0)


@pytest.mark.parametrize(
    "y_reverse, top, bottom",
    [
        (False, 5.0, 0.0),  # y-up: top is the plot max
        (True, 0.0, 5.0),  # top-down: top is the plot min
    ],
)
def test_semantic_edges(y_reverse: bool, top: float, bottom: float) -> None:
    # --- arrange ----------------------
    canvas = _canvas(y_reverse=y_reverse)

    # --- act / assert -----------------
    assert canvas.top == top
    assert canvas.bottom == bottom
    assert canvas.left == 0.0
    assert canvas.right == 10.0


def test_aspect_ratio() -> None:
    # --- arrange ----------------------
    canvas = _canvas()  # x: 1 plot unit -> 0.1 ax units; y: 1 plot unit -> 0.2 ax units

    # --- act / assert -----------------
    assert canvas.aspect_ratio() == pytest.approx(0.5)


# ==================================================================================================
#  sub_region()
# ==================================================================================================
def test_sub_region_maps_plot_block_to_ax_block() -> None:
    # --- arrange ----------------------
    canvas = _canvas()

    # --- act --------------------------
    child = canvas.sub_region(XYZRange(x=Range(0.0, 5.0), y=Range(0.0, 2.5), z=Range(0.0, 0.5)))

    # --- assert -----------------------
    assert child.xyz.x == Range(0.0, 0.5)
    assert child.xyz.y == Range(0.0, 0.5)
    assert child.xyz.z == Range(10.0, 15.0)


def test_sub_region_handles_reversed_y() -> None:
    # --- arrange ----------------------
    canvas = _canvas(y_reverse=True)

    # --- act --------------------------
    child = canvas.sub_region(XYZRange(x=Range(0.0, 10.0), y=Range(0.0, 1.0), z=Range(0.0, 1.0)))

    # --- assert -----------------------
    assert child.xyz.y.min == pytest.approx(0.8)  # top plot rows sit at high ax y
    assert child.xyz.y.max == pytest.approx(1.0)


def test_sub_region_out_of_bounds_raises() -> None:
    # --- arrange ----------------------
    canvas = _canvas()

    # --- act / assert -----------------
    with pytest.raises(LayoutError, match="not contained"):
        canvas.sub_region(XYZRange(x=Range(0.0, 11.0), y=Range(0.0, 5.0), z=Range(0.0, 1.0)))


# ==================================================================================================
#  Drawing - lines
# ==================================================================================================
def test_plot_transforms_coordinates_and_zorder() -> None:
    # --- arrange ----------------------
    ax = Mock()
    canvas = _canvas(ax, y_reverse=True)

    # --- act --------------------------
    canvas.plot([0.0, 10.0], [0.0, 5.0], LineStyle(zorder=0.5))

    # --- assert -----------------------
    args, kwargs = ax.plot.call_args
    assert args[0] == pytest.approx([0.0, 1.0])
    assert args[1] == pytest.approx([1.0, 0.0])  # reversed y
    assert kwargs["zorder"] == pytest.approx(15.0)  # z 0.5 in [0,1] -> 15 in [10,20]


def test_hline_defaults_to_full_x_span() -> None:
    # --- arrange ----------------------
    ax = Mock()
    canvas = _canvas(ax)

    # --- act --------------------------
    canvas.hline(2.5, LineStyle())

    # --- assert -----------------------
    args, _ = ax.plot.call_args
    assert args[0] == pytest.approx([0.0, 1.0])
    assert args[1] == pytest.approx([0.5, 0.5])


def test_vline_multiple_values_and_partial_span() -> None:
    # --- arrange ----------------------
    ax = Mock()
    canvas = _canvas(ax)

    # --- act --------------------------
    canvas.vline([2.0, 8.0], LineStyle(), y_min=0.0, y_max=2.5)

    # --- assert -----------------------
    assert ax.plot.call_count == 2
    first_args, _ = ax.plot.call_args_list[0]
    assert first_args[0] == pytest.approx([0.2, 0.2])
    assert first_args[1] == pytest.approx([0.0, 0.5])


def test_plot_sample_transforms_segment() -> None:
    # --- arrange ----------------------
    ax = Mock()
    canvas = _canvas(ax)

    # --- act --------------------------
    canvas.plot_sample(x_min=0.0, x_max=10.0, y=2.5, style=LineStyle(marker="o"))

    # --- assert -----------------------
    assert ax.plot.call_count == 2  # segment + centered marker
    segment_args, _ = ax.plot.call_args_list[0]
    assert segment_args[0] == pytest.approx([0.0, 1.0])
    assert segment_args[1] == pytest.approx([0.5, 0.5])


# ==================================================================================================
#  Drawing - shapes & text
# ==================================================================================================
def test_rectangle_normalizes_corners_under_reversal() -> None:
    # --- arrange ----------------------
    ax = Mock()
    canvas = _canvas(ax, y_reverse=True)

    # --- act --------------------------
    canvas.rectangle(0.0, 5.0, 0.0, 2.5, fill_color=(0.9, 0.9, 0.9), zorder=0.5)

    # --- assert -----------------------
    rect = ax.add_patch.call_args.args[0]
    assert rect.get_xy() == pytest.approx((0.0, 0.5))  # y flipped, corners re-normalized
    assert rect.get_width() == pytest.approx(0.5)
    assert rect.get_height() == pytest.approx(0.5)
    assert rect.get_zorder() == pytest.approx(15.0)


def test_rectangle_edge_style() -> None:
    # --- arrange ----------------------
    ax = Mock()
    canvas = _canvas(ax)

    # --- act --------------------------
    canvas.rectangle(0.0, 1.0, 0.0, 1.0, fill_color="white", edge_style=LineStyle(color=(1.0, 0.0, 0.0), width=2.0))

    # --- assert -----------------------
    rect = ax.add_patch.call_args.args[0]
    assert rect.get_linewidth() == pytest.approx(2.0)


def test_text_maps_coordinates_alignment_and_style() -> None:
    # --- arrange ----------------------
    ax = Mock()
    canvas = _canvas(ax)

    # --- act --------------------------
    canvas.text(5.0, 2.5, "hello", TextStyle(size=12.0), h_align=HAlign.RIGHT, v_align=VAlign.FILL, zorder=1.0)

    # --- assert -----------------------
    _, kwargs = ax.text.call_args
    assert kwargs["x"] == pytest.approx(0.5)
    assert kwargs["y"] == pytest.approx(0.5)
    assert kwargs["s"] == "hello"
    assert kwargs["ha"] == "right"
    assert kwargs["va"] == "center"  # FILL falls back to center
    assert kwargs["fontsize"] == 12.0
    assert kwargs["zorder"] == pytest.approx(20.0)


def test_text_default_zorder_is_local_z_center() -> None:
    # --- arrange ----------------------
    ax = Mock()
    canvas = _canvas(ax)

    # --- act --------------------------
    canvas.text(0.0, 0.0, "x")

    # --- assert -----------------------
    _, kwargs = ax.text.call_args
    assert kwargs["zorder"] == pytest.approx(15.0)


# ==================================================================================================
#  Non-linear guards
# ==================================================================================================
def test_delta_based_operations_raise_on_non_linear_canvas() -> None:
    # --- arrange ----------------------
    canvas = _canvas(x_log=True)

    # --- act / assert -----------------
    with pytest.raises(ValueError, match="delta-based"):
        canvas.text_size("hello", TextStyle())
    with pytest.raises(ValueError, match="delta-based"):
        canvas.rotated_text_aspect(45.0)
    with pytest.raises(ValueError, match="delta-based"):
        canvas.aspect_ratio()


def test_non_linear_canvas_still_plots() -> None:
    # --- arrange ----------------------
    ax = Mock()
    canvas = _canvas(ax, x_log=True)

    # --- act --------------------------
    canvas.plot([1.0, 10.0], [0.0, 5.0], LineStyle())

    # --- assert -----------------------
    args, _ = ax.plot.call_args
    assert args[0] == pytest.approx([0.0, 1.0])  # log x: decade 1..10 spans the full ax range
