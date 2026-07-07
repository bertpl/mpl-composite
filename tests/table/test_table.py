from __future__ import annotations

import pytest

from mpl_composite import CompositeFigure, HAlign, Table, TableColumn, TableLayout
from mpl_composite.table import ColumnGroup

# --- shared example geometry: 2 groups, 3 columns, 4 rows -----------------------------------------
_N_ROWS = 4
_ROW_HEIGHT = 0.05
_HEADER_ROWS = 1.0
_FOOTER_ROWS = 2.0


def _make_columns() -> tuple[TableColumn, TableColumn, TableColumn]:
    return TableColumn(width=0.2, h_align=HAlign.LEFT), TableColumn(width=0.1), TableColumn(width=0.1)


def _make_table(*cols: TableColumn, **kwargs: object) -> Table:
    groups = (ColumnGroup(columns=(cols[0],)), ColumnGroup(columns=cols[1:]))
    return Table(  # type: ignore[arg-type]
        _N_ROWS, _ROW_HEIGHT, groups, header_rows=_HEADER_ROWS, footer_rows=_FOOTER_ROWS, **kwargs
    )


class _LayoutCapture(Table):
    """Table subclass that records the TableLayout handed to draw_content()."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.captured: TableLayout | None = None

    def draw_content(self, table: TableLayout) -> None:
        self.captured = table


def _render_capture(*cols: TableColumn, **kwargs: object) -> TableLayout:
    groups = (ColumnGroup(columns=(cols[0],)), ColumnGroup(columns=cols[1:]))
    table = _LayoutCapture(  # type: ignore[arg-type]
        _N_ROWS, _ROW_HEIGHT, groups, header_rows=_HEADER_ROWS, footer_rows=_FOOTER_ROWS, **kwargs
    )
    fig = CompositeFigure()
    fig.add(0, 0, table)
    fig.render()
    assert table.captured is not None
    return table.captured


# ==================================================================================================
#  Construction
# ==================================================================================================
@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_rows": 0},
        {"row_height": 0.0},
        {"row_height": -1.0},
        {"groups": ()},
        {"header_rows": -1.0},
        {"footer_rows": -0.5},
    ],
)
def test_table_constructor_validation(kwargs: dict) -> None:
    # --- arrange ----------------------
    defaults = {
        "n_rows": _N_ROWS,
        "row_height": _ROW_HEIGHT,
        "groups": (ColumnGroup(columns=(TableColumn(width=0.1),)),),
    }

    # --- act / assert -----------------
    with pytest.raises(ValueError):
        Table(**(defaults | kwargs))


def test_table_rejects_reused_column_object() -> None:
    # --- arrange ----------------------
    col = TableColumn(width=0.1)

    # --- act / assert -----------------
    with pytest.raises(ValueError, match="only once"):
        Table(_N_ROWS, _ROW_HEIGHT, (ColumnGroup(columns=(col, col)),))


# ==================================================================================================
#  Measurement & canvas geometry
# ==================================================================================================
def test_table_measure() -> None:
    # --- arrange ----------------------
    table = _make_table(*_make_columns())

    # --- act --------------------------
    size = table.measure()

    # --- assert -----------------------
    assert size.x == pytest.approx(0.4)  # summed column widths
    assert size.y == pytest.approx(_ROW_HEIGHT * (_HEADER_ROWS + _N_ROWS + _FOOTER_ROWS))
    assert size.z == 1.0


def test_table_canvas_is_top_down_row_coordinates() -> None:
    # --- act --------------------------
    layout = _render_capture(*_make_columns())

    # --- assert -----------------------
    canvas = layout.canvas
    assert canvas.x.min == 0.0
    assert canvas.x.max == pytest.approx(0.4)
    assert canvas.y.min == pytest.approx(-_HEADER_ROWS)
    assert canvas.y.max == pytest.approx(_N_ROWS + _FOOTER_ROWS)
    assert canvas.top == pytest.approx(-_HEADER_ROWS)  # reversed: header above row 0
    assert canvas.bottom == pytest.approx(_N_ROWS + _FOOTER_ROWS)


# ==================================================================================================
#  TableLayout geometry helpers
# ==================================================================================================
def test_table_layout_column_range() -> None:
    # --- arrange ----------------------
    col_a, col_b, col_c = _make_columns()
    layout = _render_capture(col_a, col_b, col_c)

    # --- act / assert -----------------
    assert (layout.column_range(col_a).min, layout.column_range(col_a).max) == (0.0, 0.2)
    assert (layout.column_range(col_b).min, layout.column_range(col_b).max) == (0.2, pytest.approx(0.3))
    assert (layout.column_range(col_c).min, layout.column_range(col_c).max) == (pytest.approx(0.3), 0.4)


def test_table_layout_column_range_rejects_foreign_column() -> None:
    # --- arrange ----------------------
    layout = _render_capture(*_make_columns())

    # --- act / assert -----------------
    with pytest.raises(KeyError):
        layout.column_range(TableColumn(width=0.1))


def test_table_layout_row_range() -> None:
    # --- arrange ----------------------
    layout = _render_capture(*_make_columns())

    # --- act --------------------------
    row = layout.row_range(2)

    # --- assert -----------------------
    assert (row.min, row.max) == (2.0, 3.0)


@pytest.mark.parametrize("i_row", [-1, _N_ROWS])
def test_table_layout_row_range_validation(i_row: int) -> None:
    # --- arrange ----------------------
    layout = _render_capture(*_make_columns())

    # --- act / assert -----------------
    with pytest.raises(ValueError, match="i_row"):
        layout.row_range(i_row)


# ==================================================================================================
#  Content drawing (via rendered matplotlib artists)
# ==================================================================================================
class _ContentTable(Table):
    """Fills one cell per column plus a single-column and a spanned title."""

    def __init__(self, cols: tuple[TableColumn, ...], **kwargs: object) -> None:
        groups = (ColumnGroup(columns=(cols[0],)), ColumnGroup(columns=cols[1:]))
        super().__init__(_N_ROWS, _ROW_HEIGHT, groups, header_rows=_HEADER_ROWS, footer_rows=_FOOTER_ROWS, **kwargs)  # type: ignore[arg-type]
        self._columns = cols

    def draw_content(self, table: TableLayout) -> None:
        for i_col, col in enumerate(self._columns):
            table.cell_text(0, col, f"cell {i_col}")
        table.col_title(self._columns[0], "name")
        table.col_title(self._columns[1:], "metrics")


def test_table_draw_content_renders_texts() -> None:
    # --- arrange ----------------------
    table = _ContentTable(_make_columns())
    fig = CompositeFigure()
    fig.add(0, 0, table)

    # --- act --------------------------
    rendered = fig.render()

    # --- assert -----------------------
    texts = {artist.get_text(): artist for artist in rendered.axes[0].texts}
    assert set(texts) == {"cell 0", "cell 1", "cell 2", "name", "metrics"}
    assert texts["cell 0"].get_horizontalalignment() == "left"  # column h_align honored
    assert texts["cell 1"].get_horizontalalignment() == "center"
    assert texts["name"].get_horizontalalignment() == "left"  # single-column title: its alignment
    assert texts["metrics"].get_horizontalalignment() == "center"  # spanned title: centered
    assert texts["name"].get_fontweight() == "bold"


def test_table_cell_margin_insets_edge_aligned_text() -> None:
    # --- arrange ----------------------
    def cell0_x(cell_margin: float) -> float:
        fig = CompositeFigure()
        fig.add(0, 0, _ContentTable(_make_columns(), cell_margin=cell_margin))
        rendered = fig.render()
        texts = {artist.get_text(): artist for artist in rendered.axes[0].texts}
        return texts["cell 0"].get_position()[0]

    # --- act / assert -----------------
    # Both figures share their geometry, so axis coordinates are comparable:
    # the LEFT-aligned cell text shifts right by the margin.
    assert cell0_x(0.01) > cell0_x(0.0)


def test_table_furniture_is_drawn() -> None:
    # --- arrange ----------------------
    table = _make_table(*_make_columns())
    fig = CompositeFigure()
    fig.add(0, 0, table)

    # --- act --------------------------
    rendered = fig.render()

    # --- assert -----------------------
    ax = rendered.axes[0]
    assert len(ax.patches) == 2  # bands on rows 0 and 2
    # grid: 2 horizontal borders + 3 major verticals (group edges) + 1 minor vertical
    assert len(ax.lines) == 6
