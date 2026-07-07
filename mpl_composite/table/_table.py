"""The table element: banded rows, grouped columns, and the draw_content() hook."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mpl_composite.elements import Element
from mpl_composite.geometry import XYZ, LinearGrid, Range, XYZRange
from mpl_composite.style import DEFAULT_THEME
from mpl_composite.transforms import Transform, XYZTransform

from ._table_layout import TableLayout

if TYPE_CHECKING:
    from collections.abc import Sequence

    from mpl_composite.canvas import Region
    from mpl_composite.elements import Layout
    from mpl_composite.style import Theme

    from ._column import ColumnGroup

# Local z levels (the element's z range is (0, 1)); content drawn through
# TableLayout defaults to the range center, above all table furniture.
_Z_BANDS = 0.05
_Z_GRID_MINOR = 0.10
_Z_GRID_MAJOR = 0.15


class Table(Element):
    """n_rows uniform-height rows x explicitly declared column groups.

    draw() renders banded row backgrounds and the major/minor grid (group
    boundaries major), then calls draw_content(). Subclass and override
    draw_content() to fill cells.

    Plot coordinates: x runs over summed column widths, y is the row index
    top-down — row i spans y in [i, i+1], header rows sit at negative y,
    footer rows below y = n_rows.
    """

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(
        self,
        n_rows: int,
        row_height: float,
        groups: Sequence[ColumnGroup],
        *,
        cell_margin: float = 0.0,
        header_rows: float = 2.0,
        footer_rows: float = 4.0,
        theme: Theme = DEFAULT_THEME,
    ) -> None:
        """Declare the table geometry.

        Args:
            n_rows: Number of data rows.
            row_height: Height of one row, in layout units.
            groups: The column groups, in left-to-right order.
            cell_margin: Horizontal text inset from a cell edge, in the same units as column widths.
            header_rows: Empty row heights above the data (column titles live here).
            footer_rows: Empty row heights below the data (skewed names live here).
            theme: Style vocabulary for bands, grid, and default text.

        Raises:
            ValueError: On a non-positive n_rows/row_height, no groups, negative
                header/footer rows, or a column object declared twice.
        """
        if n_rows < 1:
            raise ValueError(f"n_rows must be >= 1 (here: {n_rows}).")
        if row_height <= 0:
            raise ValueError(f"row_height must be > 0 (here: {row_height}).")
        if not groups:
            raise ValueError("Table requires at least one column group.")
        if header_rows < 0 or footer_rows < 0:
            raise ValueError(f"header_rows and footer_rows must be >= 0 (here: ({header_rows}, {footer_rows})).")

        self._n_rows = n_rows
        self._row_height = row_height
        self._groups = tuple(groups)
        self._cell_margin = cell_margin
        self._header_rows = header_rows
        self._footer_rows = footer_rows
        self._theme = theme

        columns = [column for group in self._groups for column in group.columns]
        try:
            self._cols = LinearGrid(keys=columns, sizes=[column.width for column in columns])
        except ValueError as error:
            raise ValueError("each column object may appear in the table only once.") from error

    # --------------------------------------------------------------------------
    #  Element lifecycle
    # --------------------------------------------------------------------------
    def measure(self) -> XYZ:
        """Summed column widths x row_height-scaled total rows, with a unit z extent."""
        n_rows_total = self._header_rows + self._n_rows + self._footer_rows
        return XYZ(self._cols.span.size, self._row_height * n_rows_total, 1.0)

    def _plot_ranges(self, size: XYZ) -> XYZRange:
        """X over summed column widths; y in row indices, header above, footer below."""
        return XYZRange(
            x=self._cols.span,
            y=Range(-self._header_rows, self._n_rows + self._footer_rows),
            z=Range(0.0, size.z),
        )

    def _transforms(self, plot: XYZRange, region: Region) -> XYZTransform:
        """Table plot y runs top-down: the y transform is reversed."""
        return XYZTransform(
            x=Transform.linear(plot.x, region.xyz.x),
            y=Transform.linear(plot.y, region.xyz.y, reverse=True),
            z=Transform.linear(plot.z, region.xyz.z),
        )

    def draw(self, layout: Layout) -> None:
        """Banded row backgrounds, the major/minor grid, then draw_content()."""
        canvas = layout.canvas
        self._draw_bands(layout)
        self._draw_grid(layout)
        self.draw_content(
            TableLayout(
                canvas=canvas,
                cols=self._cols,
                n_rows=self._n_rows,
                cell_margin=self._cell_margin,
                header_rows=self._header_rows,
                footer_rows=self._footer_rows,
                theme=self._theme,
            )
        )

    def draw_content(self, table: TableLayout) -> None:
        """Override hook: fill cells, titles, embedded plots. Default: nothing."""

    # --------------------------------------------------------------------------
    #  Table furniture
    # --------------------------------------------------------------------------
    def _draw_bands(self, layout: Layout) -> None:
        """Background band on every even data row."""
        canvas = layout.canvas
        for i_row in range(0, self._n_rows, 2):
            canvas.rectangle(
                canvas.x.min,
                canvas.x.max,
                float(i_row),
                float(i_row + 1),
                fill_color=self._theme.band_color,
                zorder=_Z_BANDS,
            )

    def _draw_grid(self, layout: Layout) -> None:
        """Top/bottom borders plus vertical lines: group boundaries major, the rest minor."""
        canvas = layout.canvas
        major = self._theme.border_major.modify(zorder=_Z_GRID_MAJOR)
        minor = self._theme.border_minor.modify(zorder=_Z_GRID_MINOR)

        canvas.hline([0.0, float(self._n_rows)], major)

        major_x = sorted(
            {self._cols[group.columns[0]].min for group in self._groups}
            | {self._cols[group.columns[-1]].max for group in self._groups}
        )
        minor_x = [x for x in self._cols.boundaries() if x not in major_x]
        canvas.vline(major_x, major, y_min=0.0, y_max=float(self._n_rows))
        canvas.vline(minor_x, minor, y_min=0.0, y_max=float(self._n_rows))
