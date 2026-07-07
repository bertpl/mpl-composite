"""The draw-time facade handed to Table.draw_content(): cell-aware drawing helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mpl_composite.canvas import Canvas
from mpl_composite.geometry import HAlign, Range, VAlign, XYZRange
from mpl_composite.style import FontWeight
from mpl_composite.transforms import Transform, XYZTransform

from ._column import LABEL_ANGLE_DEG, TableColumn

if TYPE_CHECKING:
    from collections.abc import Sequence

    from mpl_composite.geometry import LinearGrid
    from mpl_composite.style import TextStyle, Theme

    from ._column import ColumnGroup, PlottingColumn

# Column titles sit this many row heights above the top data row.
_TITLE_LIFT = 0.1

# Skewed column names sit this many row heights below the bottom data row.
_SKEWED_NAME_DROP = 0.2

# The z slice of the table's local (0, 1) range handed to embedded plot columns,
# so their content sits above the table's bands and grid even at the LineStyle
# default zorder of 0.
_COLUMN_Z = Range(0.3, 1.0)

# Local z levels on the table canvas (see the hosting table element for the
# furniture levels these sit above).
_Z_LEADER_MINOR = 0.10
_Z_LEADER_MAJOR = 0.15


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
    #  Embedded plot columns & skewed names
    # --------------------------------------------------------------------------
    def column_canvas(self, col: PlottingColumn) -> Canvas:
        """Data-coordinate canvas for an embedded plot column — draw data content on it directly.

        X binds through the column's axis (scale-aware); y runs in row indices
        top-down, row i's center at y = i, with the data band spanning
        y in [-0.5, n_rows - 0.5]. Y values past the band extrapolate into the
        table's header/footer rows, which is how col.draw_decorations() draws
        tick labels below the data.

        Raises:
            KeyError: On a column that is not part of the table.
        """
        region = self.canvas.sub_region(XYZRange(x=self._cols[col], y=Range(0.0, float(self._n_rows)), z=_COLUMN_Z))
        return Canvas(
            region,
            XYZTransform(
                x=col.axis.transform(region.xyz.x),
                y=Transform.linear(Range(-0.5, self._n_rows - 0.5), region.xyz.y, reverse=True),
                z=Transform.linear(Range(0.0, 1.0), region.xyz.z),
            ),
        )

    def skewed_col_names(self, group: ColumnGroup, names: Sequence[str], *, style: TextStyle | None = None) -> None:
        """Rotated names below the table with slanted leader lines (needs footer_rows > 0).

        Leader lines extend the group's column boundaries into the footer,
        slanted parallel to the rotated names: group edges major, interior
        boundaries minor.

        Raises:
            KeyError: On a column that is not part of the table.
            ValueError: On a names/columns length mismatch, or when the table
                has no footer rows to draw into.
        """
        if len(names) != len(group.columns):
            raise ValueError(f"names and group columns must be parallel ({len(names)} vs {len(group.columns)}).")
        if self._footer_rows <= 0:
            raise ValueError("skewed column names need footer_rows > 0 to draw into.")

        # --- leader lines ---------------------------------
        y_top, y_bottom = float(self._n_rows), self._n_rows + self._footer_rows
        x_delta = self._footer_rows * self.canvas.rotated_text_aspect(LABEL_ANGLE_DEG)
        edges = {self._cols[group.columns[0]].min, self._cols[group.columns[-1]].max}
        boundaries = {self._cols[column].min for column in group.columns} | edges
        major = self._theme.border_major.modify(zorder=_Z_LEADER_MAJOR)
        minor = self._theme.border_minor.modify(zorder=_Z_LEADER_MINOR)
        for x in boundaries:
            self.canvas.plot([x, x - x_delta], [y_top, y_bottom], major if x in edges else minor)

        # --- names ----------------------------------------
        name_style = (style if style is not None else self._theme.text).modify(rotation_deg=LABEL_ANGLE_DEG)
        for column, name in zip(group.columns, names, strict=True):
            x = self._cols[column].center
            self.canvas.text(x, y_top + _SKEWED_NAME_DROP, name, name_style, h_align=HAlign.RIGHT, v_align=VAlign.TOP)

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
