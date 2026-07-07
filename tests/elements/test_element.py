from unittest.mock import Mock

from mpl_composite.canvas import Region
from mpl_composite.geometry import Range, XYZRange

from ._probe import Probe


def _region(ax=None) -> Region:
    return Region(
        ax=ax if ax is not None else Mock(),
        xyz=XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 10.0)),
    )


def test_place_builds_canvas_over_declared_plot_ranges() -> None:
    # --- arrange ----------------------
    probe = Probe(x_size=4.0, y_size=2.0, z_size=1.0)

    # --- act --------------------------
    layout = probe.place(_region())

    # --- assert -----------------------
    assert layout.canvas.x == Range(0.0, 4.0)
    assert layout.canvas.y == Range(0.0, 2.0)
    assert layout.canvas.z == Range(0.0, 1.0)
    assert layout.children == ()


def test_default_transforms_are_not_reversed() -> None:
    # --- arrange ----------------------
    probe = Probe(y_size=2.0)

    # --- act --------------------------
    layout = probe.place(_region())

    # --- assert -----------------------
    assert layout.canvas.top == 2.0  # y-up by default
    assert layout.canvas.bottom == 0.0


def test_draw_receives_the_layout() -> None:
    # --- arrange ----------------------
    probe = Probe()
    layout = probe.place(_region())

    # --- act --------------------------
    probe.draw(layout)

    # --- assert -----------------------
    assert probe.drawn_with is layout


def test_debug_boundaries_draw_a_dotted_outline() -> None:
    # --- arrange ----------------------
    ax = Mock()
    probe = Probe(x_size=2.0, y_size=1.0)
    layout = probe.place(_region(ax))

    # --- act --------------------------
    probe.draw_debug_boundaries(layout, alpha=0.5)

    # --- assert -----------------------
    args, kwargs = ax.plot.call_args
    assert args[0] == [0.0, 1.0, 1.0, 0.0, 0.0]  # closed rectangle in ax coords
    assert kwargs["linestyle"] == ":"
    assert kwargs["alpha"] == 0.5
