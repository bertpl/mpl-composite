"""The grid container element."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mpl_composite.geometry import HAlign, LinearGrid, Margin, Range, VAlign, XYZ, XYZRange
from mpl_composite.transforms import Transform, XYZTransform

from ._element import Element

if TYPE_CHECKING:
    from mpl_composite.canvas import Canvas, Region

    from ._layout import Layout


# ==================================================================================================
#  _ChildSlot
# ==================================================================================================
@dataclass(frozen=True)
class _ChildSlot:
    """One child with its grid position, alignment, and margin.

    All geometry here is expressed in the composite's plot coordinates, which
    run top-down in y (row 0 at y = 0, the visual top).
    """

    element: Element
    i_row: int
    i_col: int
    h_align: HAlign
    v_align: VAlign
    margin: Margin

    def gross_size(self) -> XYZ:
        """Child size including 2-D margins (z takes no margin)."""
        size = self.element.measure()
        return XYZ(size.x + self.margin.width, size.y + self.margin.height, size.z)

    def fit(self, cell: XYZRange) -> XYZRange:
        """Apply margin + alignment inside the cell -> the child's plot-coordinate block."""
        size = self.element.measure()
        x_available = Range(cell.x.min + self.margin.left, cell.x.max - self.margin.right)
        y_available = Range(cell.y.min + self.margin.top, cell.y.max - self.margin.bottom)  # top-down: top at min
        return XYZRange(
            x=self.h_align.fit(x_available, size.x),
            y=self.v_align.fit(y_available, size.y, top_at_max=False),
            z=cell.z,
        )


# ==================================================================================================
#  Composite
# ==================================================================================================
class Composite(Element):
    """Grid container: children in (row, col) cells; rows top-down, columns left-right.

    Cell sizes are the max over occupants (table-layout style); children are
    stacked in z in insertion order, each getting a disjoint z sub-range, so
    nested layering never collides across siblings.
    """

    # --------------------------------------------------------------------------
    #  Composition
    # --------------------------------------------------------------------------
    def __init__(self) -> None:
        """Start with an empty grid."""
        self._slots: list[_ChildSlot] = []

    def add(
        self,
        i_row: int,
        i_col: int,
        element: Element,
        *,
        h_align: HAlign = HAlign.CENTER,
        v_align: VAlign = VAlign.CENTER,
        margin: float | Margin = 0.0,
    ) -> None:
        """Add a child element to grid cell (i_row, i_col); a float margin means uniform on all sides.

        Raises:
            ValueError: On negative grid indices.
        """
        if i_row < 0 or i_col < 0:
            raise ValueError(f"i_row and i_col must be >= 0 (here: ({i_row}, {i_col})).")
        if isinstance(margin, int | float):
            margin = Margin.uniform(margin)
        self._slots.append(_ChildSlot(element, i_row, i_col, h_align, v_align, margin))

    @property
    def n_rows(self) -> int:
        """Number of grid rows (1 + highest occupied row index)."""
        return 1 + max((slot.i_row for slot in self._slots), default=-1)

    @property
    def n_cols(self) -> int:
        """Number of grid columns (1 + highest occupied column index)."""
        return 1 + max((slot.i_col for slot in self._slots), default=-1)

    # --------------------------------------------------------------------------
    #  Element lifecycle
    # --------------------------------------------------------------------------
    def measure(self) -> XYZ:
        """Total grid size: summed max-based column widths / row heights, summed child z sizes."""
        cols, rows, z_grid = self._grids()
        return XYZ(cols.span.size, rows.span.size, z_grid.span.size)

    def draw(self, layout: Layout) -> None:
        """Draw every child with its own layout."""
        for slot, child_layout in zip(self._slots, layout.children, strict=True):
            slot.element.draw(child_layout)

    def _transforms(self, plot: XYZRange, region: Region) -> XYZTransform:
        """Composite plot y runs top-down: the y transform is reversed."""
        return XYZTransform(
            x=Transform.linear(plot.x, region.xyz.x),
            y=Transform.linear(plot.y, region.xyz.y, reverse=True),
            z=Transform.linear(plot.z, region.xyz.z),
        )

    def _place_children(self, canvas: Canvas) -> tuple[Layout, ...]:
        """Per child: grid cell -> margin/alignment fit -> sub-region -> recursive place."""
        cols, rows, z_grid = self._grids()
        layouts = []
        for i_slot, slot in enumerate(self._slots):
            cell = XYZRange(x=cols[slot.i_col], y=rows[slot.i_row], z=z_grid.range_by_index(i_slot))
            layouts.append(slot.element.place(canvas.sub_region(slot.fit(cell))))
        return tuple(layouts)

    # --------------------------------------------------------------------------
    #  Internal
    # --------------------------------------------------------------------------
    def _grids(self) -> tuple[LinearGrid, LinearGrid, LinearGrid]:
        """Pure derivation of the (cols, rows, z) grids from the current children.

        Called from both measure() and _place_children() — recomputed, never
        stored, so measurement stays side-effect-free.
        """
        col_sizes = [0.0] * self.n_cols
        row_sizes = [0.0] * self.n_rows
        z_sizes = []
        for slot in self._slots:
            gross = slot.gross_size()
            col_sizes[slot.i_col] = max(col_sizes[slot.i_col], gross.x)
            row_sizes[slot.i_row] = max(row_sizes[slot.i_row], gross.y)
            z_sizes.append(gross.z)
        return (
            LinearGrid(keys=range(self.n_cols), sizes=col_sizes),
            LinearGrid(keys=range(self.n_rows), sizes=row_sizes),
            LinearGrid(keys=range(len(z_sizes)), sizes=z_sizes),
        )

    # --------------------------------------------------------------------------
    #  Debugging
    # --------------------------------------------------------------------------
    def draw_debug_boundaries(self, layout: Layout, *, alpha: float = 0.8) -> None:
        """Own outline, then children's recursively with fading alpha."""
        super().draw_debug_boundaries(layout, alpha=alpha)
        for slot, child_layout in zip(self._slots, layout.children, strict=True):
            slot.element.draw_debug_boundaries(child_layout, alpha=0.8 * alpha)
