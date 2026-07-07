import pytest

from mpl_composite.geometry import LinearGrid, Range


# ==================================================================================================
#  Construction & validation
# ==================================================================================================
def test_grid_cumulative_ranges() -> None:
    # --- act --------------------------
    grid = LinearGrid(keys=["a", "b", "c"], sizes=[1.0, 2.0, 0.5])

    # --- assert -----------------------
    assert grid["a"] == Range(0.0, 1.0)
    assert grid["b"] == Range(1.0, 3.0)
    assert grid["c"] == Range(3.0, 3.5)


@pytest.mark.parametrize(
    "keys, sizes, match",
    [
        (["a", "b"], [1.0], "equal length"),
        (["a", "a"], [1.0, 2.0], "unique"),
        (["a"], [-1.0], "non-negative"),
    ],
)
def test_grid_rejects_invalid_input(keys: list, sizes: list, match: str) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match=match):
        LinearGrid(keys=keys, sizes=sizes)


def test_grid_allows_zero_sized_cells() -> None:
    # --- act --------------------------
    grid = LinearGrid(keys=[0, 1, 2], sizes=[1.0, 0.0, 2.0])

    # --- assert -----------------------
    assert grid[1] == Range(1.0, 1.0)
    assert grid[2] == Range(1.0, 3.0)


# ==================================================================================================
#  Cell access
# ==================================================================================================
def test_grid_len_and_index_access() -> None:
    # --- arrange ----------------------
    grid = LinearGrid(keys=["a", "b"], sizes=[1.0, 2.0])

    # --- act / assert -----------------
    assert len(grid) == 2
    assert grid.range_by_index(0) == Range(0.0, 1.0)
    assert grid.range_by_index(1) == Range(1.0, 3.0)


def test_grid_unknown_key_raises() -> None:
    # --- arrange ----------------------
    grid = LinearGrid(keys=["a"], sizes=[1.0])

    # --- act / assert -----------------
    with pytest.raises(KeyError):
        grid["nope"]


# ==================================================================================================
#  Grid-wide queries
# ==================================================================================================
def test_grid_boundaries() -> None:
    # --- arrange ----------------------
    grid = LinearGrid(keys=["a", "b", "c"], sizes=[1.0, 2.0, 0.5])

    # --- act / assert -----------------
    assert grid.boundaries() == [0.0, 1.0, 3.0, 3.5]
    assert grid.boundaries(include_edges=False) == [1.0, 3.0]


def test_grid_span() -> None:
    # --- arrange ----------------------
    grid = LinearGrid(keys=["a", "b"], sizes=[1.5, 2.5])

    # --- act / assert -----------------
    assert grid.span == Range(0.0, 4.0)


def test_empty_grid() -> None:
    # --- act --------------------------
    grid = LinearGrid(keys=[], sizes=[])

    # --- assert -----------------------
    assert len(grid) == 0
    assert grid.span == Range(0.0, 0.0)
    assert grid.boundaries() == []
    assert grid.boundaries(include_edges=False) == []
