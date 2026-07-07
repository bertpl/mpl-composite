import matplotlib.pyplot as plt
import pytest

from mpl_composite import CompositeFigure, LineStyle, PlotAxes, PlotAxis, ScaleLog
from mpl_composite.canvas import Canvas
from mpl_composite.plot._axis_bars import bar_thickness

_X_AXIS = PlotAxis.from_range(0.0, 10.0, label="x")
_Y_AXIS = PlotAxis.from_range(1.0, 100.0, scale=ScaleLog(), label="y")


class _Empty(PlotAxes):
    """Minimal concrete PlotAxes: draws nothing."""

    def draw_plot(self, canvas: Canvas) -> None:
        """No content."""


class _Recorder(PlotAxes):
    """Concrete PlotAxes that records the canvas handed to draw_plot."""

    canvas: Canvas | None = None

    def draw_plot(self, canvas: Canvas) -> None:
        """Record the data-coordinate canvas and draw one line through it."""
        self.canvas = canvas
        canvas.plot([1.0, 9.0], [2.0, 50.0], LineStyle())


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def test_rejects_non_positive_plot_sizes() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="> 0"):
        _Empty(_X_AXIS, _Y_AXIS, plot_width=0.0, plot_height=1.0)


def test_cannot_instantiate_without_draw_plot() -> None:
    # --- act / assert -----------------
    with pytest.raises(TypeError, match="draw_plot"):
        PlotAxes(_X_AXIS, _Y_AXIS, plot_width=1.0, plot_height=1.0)  # type: ignore[abstract]


def test_grid_shape_with_and_without_title() -> None:
    # --- act --------------------------
    titled = _Empty(_X_AXIS, _Y_AXIS, plot_width=1.0, plot_height=0.7, title="t")
    untitled = _Empty(_X_AXIS, _Y_AXIS, plot_width=1.0, plot_height=0.7)

    # --- assert -----------------------
    assert (titled.n_rows, titled.n_cols) == (3, 2)
    assert (untitled.n_rows, untitled.n_cols) == (2, 2)


def test_measure_adds_bars_around_the_plot_area() -> None:
    # --- arrange ----------------------
    plot_axes = _Empty(_X_AXIS, _Y_AXIS, plot_width=1.0, plot_height=0.7)

    # --- act --------------------------
    size = plot_axes.measure()

    # --- assert -----------------------
    assert size.x == pytest.approx(1.0 + bar_thickness(1.0, labeled=True))
    assert size.y == pytest.approx(0.7 + bar_thickness(0.7, labeled=True))


def test_draw_plot_receives_a_data_coordinate_canvas() -> None:
    # --- arrange ----------------------
    plot_axes = _Recorder(_X_AXIS, _Y_AXIS, plot_width=1.0, plot_height=0.7)
    fig = CompositeFigure()
    fig.add(0, 0, plot_axes)

    # --- act --------------------------
    fig.render()

    # --- assert -----------------------
    canvas = plot_axes.canvas
    assert canvas is not None
    assert canvas.x == _X_AXIS.range
    assert canvas.y == _Y_AXIS.range
    assert not canvas._trans.y.is_linear()  # log y binds through the axis scale


def test_render_smoke_produces_content_and_chrome() -> None:
    # --- arrange ----------------------
    plot_axes = _Recorder(_X_AXIS, _Y_AXIS, plot_width=1.0, plot_height=0.7, title="Title")
    fig = CompositeFigure()
    fig.add(0, 0, plot_axes)

    # --- act --------------------------
    rendered = fig.render()

    # --- assert -----------------------
    (ax,) = rendered.axes
    assert len(ax.lines) > 10  # grid + ticks + frame + content
    assert "Title" in [t.get_text() for t in ax.texts]
