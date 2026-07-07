import matplotlib.pyplot as plt
import pytest

from mpl_composite import Composite, CompositeFigure, Spacer, Text


def _demo_figure() -> CompositeFigure:
    """Title over a 2x2 inner grid with a spacer column."""
    fig = CompositeFigure(fig_inch_per_unit=4.0)
    fig.add(0, 0, Text(1.0, 0.15, "Demo title"))
    inner = Composite()
    inner.add(0, 0, Text(0.4, 0.1, "top left"))
    inner.add(0, 1, Spacer(0.1, 0.1))
    inner.add(1, 0, Spacer(0.1, 0.1))
    inner.add(1, 1, Text(0.4, 0.1, "bottom right"))
    fig.add(1, 0, inner, margin=0.05)
    return fig


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def test_render_returns_a_sized_figure() -> None:
    # --- arrange ----------------------
    composite_figure = _demo_figure()
    size = composite_figure.measure()

    # --- act --------------------------
    fig = composite_figure.render()

    # --- assert -----------------------
    assert fig.get_size_inches() == pytest.approx((size.x * 4.0, size.y * 4.0))


def test_render_hides_axes_chrome_and_sets_limits() -> None:
    # --- arrange ----------------------
    composite_figure = _demo_figure()
    size = composite_figure.measure()

    # --- act --------------------------
    fig = composite_figure.render()

    # --- assert -----------------------
    (ax,) = fig.axes
    assert ax.get_xlim() == (0.0, size.x)
    assert ax.get_ylim() == (0.0, size.y)
    assert list(ax.get_xticks()) == []
    assert all(not spine.get_visible() for spine in ax.spines.values())


def test_render_draws_the_content() -> None:
    # --- act --------------------------
    fig = _demo_figure().render()

    # --- assert -----------------------
    (ax,) = fig.axes
    assert {t.get_text() for t in ax.texts} == {"Demo title", "top left", "bottom right"}


def test_debug_boundaries_add_outlines() -> None:
    # --- arrange ----------------------
    plain = _demo_figure().render()
    debug = _demo_figure().render(debug_boundaries=True)

    # --- act / assert -----------------
    assert len(debug.axes[0].lines) > len(plain.axes[0].lines)


def test_render_rejects_an_empty_figure() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="empty figure"):
        CompositeFigure().render()
