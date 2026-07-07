"""The draw-time facade handed to Table.draw_content(): cell-aware drawing helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mpl_composite.geometry import HAlign, Range, VAlign
from mpl_composite.style import FontWeight

from ._column import TableColumn

if TYPE_CHECKING:
    from collections.abc import Sequence

    from mpl_composite.canvas import Canvas
    from mpl_composite.geometry import LinearGrid
    from mpl_composite.style import TextStyle, Theme

# Column titles sit this many row heights above the top data row.
_TITLE_LIFT = 0.1


class TableLayout:
    """Draw-time facade handed to draw_content(): cell-aware helpers around the table's canvas.

    Content code never does grid arithmetic. The canvas is in table plot
    coordinates: x over summed column widths, y = row index top-down.
    """

    # --------------------------------------------------------------------------
    #  Constructor
    # --------------------------------------------------------------------------
    def __init__(
        self,
        canvas: Canvas,
        cols: LinearGrid,
        n_rows: int,
        cell_margin: float,
        header_rows: float,
        footer_rows: float,
        theme: Theme,
    ) -> None:
        """Bind the facade to the hosting table's canvas and grid geometry."""
        self.canvas = canvas
        self._cols = cols
        self._n_rows = n_rows
        self._cell_margin = cell_margin
        self._header_rows = header_rows
        self._footer_rows = footer_rows
        self._theme = theme

    # --------------------------------------------------------------------------
    #  Geometry
    # --------------------------------------------------------------------------
    def column_range(self, col: TableColumn) -> Range:
        """The column's x extent in table plot coordinates.

        Raises:
            KeyError: On a column that is not part of the table.
        """
        return self._cols[col]

    def row_range(self, i_row: int) -> Range:
        """The row's y extent in table plot coordinates.

        Raises:
            ValueError: On a row index outside the data rows.
        """
        self._validate_row(i_row)
        return Range(float(i_row), float(i_row + 1))

    # --------------------------------------------------------------------------
    #  Cell drawing
    # --------------------------------------------------------------------------
    def cell_text(self, i_row: int, col: TableColumn, s: str, style: TextStyle | None = None) -> None:
        """Text in a cell, honoring the column's h_align and the cell margin.

        Raises:
            KeyError: On a column that is not part of the table.
            ValueError: On a row index outside the data rows.
        """
        x = self._aligned_x(self._cols[col], col.h_align)
        y = self.row_range(i_row).center
        self.canvas.text(x, y, s, style if style is not None else self._theme.text, h_align=col.h_align)

    def col_title(self, cols: TableColumn | Sequence[TableColumn], s: str, *, bold: bool = True) -> None:
        """Title above the top row (single column: its alignment; span: centered).

        Raises:
            KeyError: On a column that is not part of the table.
        """
        if isinstance(cols, TableColumn):
            h_align = cols.h_align
            x = self._aligned_x(self._cols[cols], h_align)
        else:
            h_align = HAlign.CENTER
            x = 0.5 * (min(self._cols[c].min for c in cols) + max(self._cols[c].max for c in cols))

        style = self._theme.text.modify(weight=FontWeight.BOLD) if bold else self._theme.text
        self.canvas.text(x, -_TITLE_LIFT, s, style, h_align=h_align, v_align=VAlign.BOTTOM)

    # --------------------------------------------------------------------------
    #  Internal
    # --------------------------------------------------------------------------
    def _aligned_x(self, x_range: Range, h_align: HAlign) -> float:
        """Text anchor x inside a column extent: cell-margin inset at the edges, center otherwise."""
        if h_align is HAlign.LEFT:
            return x_range.min + self._cell_margin
        if h_align is HAlign.RIGHT:
            return x_range.max - self._cell_margin
        return x_range.center

    def _validate_row(self, i_row: int) -> None:
        """Raise on a row index outside the data rows.

        Raises:
            ValueError: On a row index outside the data rows.
        """
        if not 0 <= i_row < self._n_rows:
            raise ValueError(f"i_row must be in [0, {self._n_rows}) (here: {i_row}).")
