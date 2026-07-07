import pytest

from mpl_composite.axis import PlotAxis
from mpl_composite.geometry import HAlign
from mpl_composite.table import ColumnGroup, PlottingColumn, TableColumn


# ==================================================================================================
#  TableColumn
# ==================================================================================================
def test_table_column_fields() -> None:
    # --- act --------------------------
    col = TableColumn(width=0.2, h_align=HAlign.LEFT)

    # --- assert -----------------------
    assert col.width == 0.2
    assert col.h_align == HAlign.LEFT


def test_table_column_default_alignment() -> None:
    # --- act --------------------------
    col = TableColumn(width=0.2)

    # --- assert -----------------------
    assert col.h_align == HAlign.CENTER


@pytest.mark.parametrize("width", [0.0, -0.1])
def test_table_column_rejects_non_positive_width(width: float) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="width"):
        TableColumn(width=width)


def test_table_column_is_frozen() -> None:
    # --- arrange ----------------------
    col = TableColumn(width=0.2)

    # --- act / assert -----------------
    with pytest.raises(AttributeError):
        col.width = 0.3  # type: ignore[misc]


def test_table_column_identity_semantics() -> None:
    # --- arrange ----------------------
    col_a = TableColumn(width=0.2)
    col_b = TableColumn(width=0.2)

    # --- assert -----------------------
    assert col_a != col_b
    assert col_a == col_a
    assert len({col_a: "a", col_b: "b"}) == 2  # distinct dict keys despite equal fields


def test_table_column_multi() -> None:
    # --- act --------------------------
    cols = TableColumn.multi(3, width=0.1, h_align=HAlign.RIGHT)

    # --- assert -----------------------
    assert len(cols) == 3
    assert all(col.width == 0.1 for col in cols)
    assert all(col.h_align == HAlign.RIGHT for col in cols)
    assert len(set(map(id, cols))) == 3  # distinct instances (each its own grid key)


def test_table_column_multi_rejects_non_positive_n() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="n must be"):
        TableColumn.multi(0, width=0.1)


# ==================================================================================================
#  PlottingColumn
# ==================================================================================================
def test_plotting_column_fields() -> None:
    # --- arrange ----------------------
    axis = PlotAxis.from_range(1.0, 100.0)

    # --- act --------------------------
    col = PlottingColumn(width=1.0, axis=axis)

    # --- assert -----------------------
    assert isinstance(col, TableColumn)
    assert col.axis is axis
    assert col.h_align == HAlign.CENTER


def test_plotting_column_axis_is_keyword_only() -> None:
    # --- act / assert -----------------
    with pytest.raises(TypeError):
        PlottingColumn(1.0, PlotAxis.from_range(1.0, 100.0))  # type: ignore[misc]


def test_plotting_column_rejects_non_positive_width() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="width"):
        PlottingColumn(width=0.0, axis=PlotAxis.from_range(1.0, 100.0))


# ==================================================================================================
#  ColumnGroup
# ==================================================================================================
def test_column_group_fields() -> None:
    # --- arrange ----------------------
    cols = TableColumn.multi(2, width=0.1)

    # --- act --------------------------
    group = ColumnGroup(columns=cols, name="properties")

    # --- assert -----------------------
    assert group.columns == cols
    assert group.name == "properties"


def test_column_group_default_name() -> None:
    # --- act --------------------------
    group = ColumnGroup(columns=(TableColumn(width=0.1),))

    # --- assert -----------------------
    assert group.name == ""


def test_column_group_preserves_order() -> None:
    # --- arrange ----------------------
    col_a, col_b, col_c = TableColumn(width=0.1), TableColumn(width=0.2), TableColumn(width=0.3)

    # --- act --------------------------
    group = ColumnGroup(columns=(col_c, col_a, col_b))

    # --- assert -----------------------
    assert group.columns == (col_c, col_a, col_b)


def test_column_group_rejects_empty() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="at least one column"):
        ColumnGroup(columns=())
