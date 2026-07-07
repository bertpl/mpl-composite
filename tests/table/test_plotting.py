from __future__ import annotations

import pytest

from mpl_composite import CompositeFigure, HAlign, LineStyle, PlotAxis, ScaleLog, Table, TableColumn, TableLayout
from mpl_composite.style import DEFAULT_THEME
from mpl_composite.table import ColumnGroup, PlottingColumn

_N_ROWS = 3
_ROW_HEIGHT = 0.05


def _make_axis() -> PlotAxis:
    return PlotAxis.from_range(1.0, 100.0, scale=ScaleLog(), label="score")


class _PlottingTable(Table):
    """Table with a text column plus a plotting column; records its draw-time layout."""

    def __init__(self, *, footer_rows: float = 2.0, decorations: bool = False) -> None:
        self.text_col = TableColumn(width=0.1, h_align=HAlign.LEFT)
        self.plot_col = PlottingColumn(width=0.5, axis=_make_axis())
        self._decorations = decorations
        super().__init__(
            _N_ROWS,
            _ROW_HEIGHT,
            (ColumnGroup(columns=(self.text_col,)), ColumnGroup(columns=(self.plot_col,))),
            header_rows=1.0,
            footer_rows=footer_rows,
        )
        self.captured: TableLayout | None = None

    def draw_content(self, table: TableLayout) -> None:
        self.captured = table
        if self._decorations:
            canvas = table.column_canvas(self.plot_col)
            self.plot_col.draw_decorations(canvas, DEFAULT_THEME)
            canvas.plot([2.0, 50.0], [0.0, float(_N_ROWS - 1)], LineStyle())


def _render(**kwargs: object) -> _PlottingTable:
    table = _PlottingTable(**kwargs)  # type: ignore[arg-type]
    fig = CompositeFigure()
    fig.add(0, 0, table)
    fig.render()
    assert table.captured is not None
    return table


# ==================================================================================================
#  column_canvas
# ==================================================================================================
def test_column_canvas_data_coordinates() -> None:
    # --- arrange ----------------------
    table = _render()
    layout = table.captured
    assert layout is not None

    # --- act --------------------------
    canvas = layout.column_canvas(table.plot_col)

    # --- assert -----------------------
    assert (canvas.x.min, canvas.x.max) == (1.0, 100.0)  # the column axis' data range
    assert (canvas.y.min, canvas.y.max) == (-0.5, _N_ROWS - 0.5)  # row centers at integer y
    assert canvas.top == -0.5  # top-down: row 0 at the top
    assert canvas.bottom == _N_ROWS - 0.5


def test_column_canvas_x_is_scale_aware() -> None:
    # --- arrange ----------------------
    table = _render()
    layout = table.captured
    assert layout is not None
    canvas = layout.column_canvas(table.plot_col)

    # --- act --------------------------
    x_lo, x_mid, x_hi = canvas._trans.x([1.0, 10.0, 100.0])

    # --- assert -----------------------
    assert x_mid - x_lo == pytest.approx(x_hi - x_mid)  # log scale: decades map to equal extents


def test_column_canvas_rejects_foreign_column() -> None:
    # --- arrange ----------------------
    layout = _render().captured
    assert layout is not None

    # --- act / assert -----------------
    with pytest.raises(KeyError):
        layout.column_canvas(PlottingColumn(width=0.5, axis=_make_axis()))


def test_column_canvas_rows_align_with_table_rows() -> None:
    # --- arrange ----------------------
    table = _render()
    layout = table.captured
    assert layout is not None
    canvas = layout.column_canvas(table.plot_col)

    # --- act / assert -----------------
    # Row i's center in data coordinates (y = i) maps to the same axis
    # coordinate as the table row's center (y = i + 0.5).
    for i_row in range(_N_ROWS):
        y_data = canvas._trans.y(float(i_row))
        y_table = layout.canvas._trans.y(i_row + 0.5)
        assert y_data == pytest.approx(y_table)


# ==================================================================================================
#  draw_decorations
# ==================================================================================================
def test_draw_decorations_renders_grid_ticks_and_labels() -> None:
    # --- arrange / act ----------------
    table = _PlottingTable(decorations=True)
    fig = CompositeFigure()
    fig.add(0, 0, table)
    rendered = fig.render()

    # --- assert -----------------------
    ax = rendered.axes[0]
    ticks = _make_axis().ticks
    texts = [artist.get_text() for artist in ax.texts]
    assert set(ticks.major_labels) <= set(texts)  # every major tick gets a skewed label
    assert "score" in texts  # the axis label
    # table furniture (2 borders + 3 group boundaries) + per-tick grid line and tick mark + the data line
    n_ticks = len(ticks.major) + len(ticks.minor)
    assert len(ax.lines) == 5 + 2 * n_ticks + 1


# ==================================================================================================
#  skewed_col_names
# ==================================================================================================
class _SkewedNamesTable(Table):
    """Single-group table that draws skewed names for all its columns."""

    def __init__(self) -> None:
        self.group = ColumnGroup(columns=TableColumn.multi(3, width=0.05), name="properties")
        super().__init__(_N_ROWS, _ROW_HEIGHT, (self.group,), footer_rows=2.0)

    def draw_content(self, table: TableLayout) -> None:
        table.skewed_col_names(self.group, ["one", "two", "three"])


def test_skewed_col_names_renders_names_and_leader_lines() -> None:
    # --- arrange ----------------------
    fig = CompositeFigure()
    fig.add(0, 0, _SkewedNamesTable())

    # --- act --------------------------
    rendered = fig.render()

    # --- assert -----------------------
    ax = rendered.axes[0]
    assert [artist.get_text() for artist in ax.texts] == ["one", "two", "three"]
    assert all(artist.get_rotation() == pytest.approx(60.0) for artist in ax.texts)
    # furniture (2 h borders + 2 major + 2 minor verticals) + 4 leader lines
    assert len(ax.lines) == 6 + 4


def test_skewed_col_names_validation() -> None:
    # --- arrange ----------------------
    table = _render(footer_rows=2.0)
    layout = table.captured
    assert layout is not None
    group = ColumnGroup(columns=(table.text_col,))

    # --- act / assert -----------------
    with pytest.raises(ValueError, match="parallel"):
        layout.skewed_col_names(group, ["a", "b"])


def test_skewed_col_names_requires_footer_rows() -> None:
    # --- arrange ----------------------
    table = _render(footer_rows=0.0)
    layout = table.captured
    assert layout is not None

    # --- act / assert -----------------
    with pytest.raises(ValueError, match="footer_rows"):
        layout.skewed_col_names(ColumnGroup(columns=(table.text_col,)), ["a"])
