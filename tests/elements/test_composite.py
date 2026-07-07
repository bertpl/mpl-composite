from unittest.mock import Mock

import pytest

from mpl_composite.canvas import Region
from mpl_composite.elements import Composite
from mpl_composite.geometry import XYZ, HAlign, Range, VAlign, XYZRange

from ._probe import Probe


def _region(x_max: float = 1.0, y_max: float = 1.0, z_max: float = 10.0) -> Region:
    return Region(ax=Mock(), xyz=XYZRange(x=Range(0.0, x_max), y=Range(0.0, y_max), z=Range(0.0, z_max)))


# ==================================================================================================
#  Composition & measurement
# ==================================================================================================
def test_add_rejects_negative_indices() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match=">= 0"):
        Composite().add(-1, 0, Probe())


def test_measure_uses_max_based_cell_sizing() -> None:
    # --- arrange ----------------------
    composite = Composite()
    composite.add(0, 0, Probe(x_size=2.0, y_size=1.0))
    composite.add(0, 1, Probe(x_size=1.0, y_size=3.0))  # taller: stretches row 0
    composite.add(1, 1, Probe(x_size=4.0, y_size=1.0))  # wider: stretches col 1

    # --- act --------------------------
    size = composite.measure()

    # --- assert -----------------------
    assert size.x == 2.0 + 4.0  # col widths: max(2, .) + max(1, 4)
    assert size.y == 3.0 + 1.0  # row heights: max(1, 3) + 1
    assert size.z == 3.0  # z sizes stack


def test_measure_includes_margins_in_cell_sizes() -> None:
    # --- arrange ----------------------
    composite = Composite()
    composite.add(0, 0, Probe(x_size=1.0, y_size=1.0), margin=0.25)

    # --- act / assert -----------------
    assert composite.measure() == XYZ(1.5, 1.5, 1.0)


def test_empty_composite_measures_zero() -> None:
    # --- act / assert -----------------
    assert Composite().measure() == XYZ(0.0, 0.0, 0.0)


# ==================================================================================================
#  Placement
# ==================================================================================================
def test_top_down_rows() -> None:
    # --- arrange ----------------------
    composite = Composite()
    top, bottom = Probe(), Probe()
    composite.add(0, 0, top)
    composite.add(1, 0, bottom)

    # --- act --------------------------
    layout = composite.place(_region())

    # --- assert -----------------------
    top_region_y = (
        layout.children[0].canvas.sub_region(XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 1.0))).xyz.y
    )
    bottom_region_y = (
        layout.children[1].canvas.sub_region(XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 1.0))).xyz.y
    )
    assert top_region_y == Range(0.5, 1.0)  # row 0 sits at high ax y (the visual top)
    assert bottom_region_y == Range(0.0, 0.5)


def test_alignment_and_margin_produce_exact_child_regions() -> None:
    # --- arrange ----------------------
    # one 1x1 child in a 1.5x1.5 composite (margin 0.25), aligned LEFT/TOP
    composite = Composite()
    child = Probe(x_size=1.0, y_size=1.0)
    composite.add(0, 0, child, h_align=HAlign.LEFT, v_align=VAlign.TOP, margin=0.25)

    # --- act --------------------------
    layout = composite.place(_region())

    # --- assert -----------------------
    child_block = (
        layout.children[0].canvas.sub_region(XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 1.0))).xyz
    )
    assert child_block.x.min == pytest.approx(0.25 / 1.5)
    assert child_block.x.max == pytest.approx(1.25 / 1.5)
    assert child_block.y.min == pytest.approx(1.0 - 1.25 / 1.5)  # TOP in a top-down grid -> high ax y
    assert child_block.y.max == pytest.approx(1.0 - 0.25 / 1.5)


def test_fill_alignment_stretches_child_over_the_cell() -> None:
    # --- arrange ----------------------
    composite = Composite()
    small = Probe(x_size=1.0, y_size=1.0)
    composite.add(0, 0, small, h_align=HAlign.FILL, v_align=VAlign.FILL)
    composite.add(1, 0, Probe(x_size=4.0, y_size=1.0))  # forces a wide column

    # --- act --------------------------
    layout = composite.place(_region())

    # --- assert -----------------------
    # the small child's unit plot range spans the full column width
    small_block = (
        layout.children[0].canvas.sub_region(XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 1.0))).xyz
    )
    assert small_block.x == Range(0.0, 1.0)


def test_sibling_z_ranges_are_disjoint() -> None:
    # --- arrange ----------------------
    composite = Composite()
    a, b = Probe(z_size=1.0), Probe(z_size=2.0)
    composite.add(0, 0, a)
    composite.add(0, 0, b)  # same cell: overlapping in x/y, stacked in z

    # --- act --------------------------
    layout = composite.place(_region())

    # --- assert -----------------------
    probe_block = XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 1.0))
    z_a = layout.children[0].canvas.sub_region(probe_block).xyz.z
    b_block = XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 2.0))
    z_b = layout.children[1].canvas.sub_region(b_block).xyz.z
    assert z_a.max <= z_b.min  # insertion order: a below b, no overlap


def test_nested_composites_place_recursively() -> None:
    # --- arrange ----------------------
    inner = Composite()
    leaf = Probe()
    inner.add(0, 0, leaf)
    outer = Composite()
    outer.add(0, 0, inner)

    # --- act --------------------------
    layout = outer.place(_region())

    # --- assert -----------------------
    assert len(layout.children) == 1
    assert len(layout.children[0].children) == 1  # the leaf's layout, nested


# ==================================================================================================
#  Drawing
# ==================================================================================================
def test_draw_dispatches_each_child_with_its_own_layout() -> None:
    # --- arrange ----------------------
    composite = Composite()
    a, b = Probe(), Probe()
    composite.add(0, 0, a)
    composite.add(0, 1, b)
    layout = composite.place(_region())

    # --- act --------------------------
    composite.draw(layout)

    # --- assert -----------------------
    assert a.drawn_with is layout.children[0]
    assert b.drawn_with is layout.children[1]


def test_debug_boundaries_recurse_with_fading_alpha() -> None:
    # --- arrange ----------------------
    ax = Mock()
    composite = Composite()
    composite.add(0, 0, Probe())
    region = Region(ax=ax, xyz=XYZRange(x=Range(0.0, 1.0), y=Range(0.0, 1.0), z=Range(0.0, 10.0)))
    layout = composite.place(region)

    # --- act --------------------------
    composite.draw_debug_boundaries(layout, alpha=1.0)

    # --- assert -----------------------
    assert ax.plot.call_count == 2  # own box + child box
    alphas = [call.kwargs["alpha"] for call in ax.plot.call_args_list]
    assert alphas == [1.0, 0.8]
