"""Declarative column specs: pure data describing table columns and their grouping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from mpl_composite.geometry import HAlign

if TYPE_CHECKING:
    from mpl_composite.axis import PlotAxis


# ==================================================================================================
#  TableColumn
# ==================================================================================================
@dataclass(frozen=True, eq=False)
class TableColumn:
    """One column spec: width in layout units + cell text alignment.

    eq=False: each declared column is a distinct grid key (identity
    semantics), so two same-width columns never collide.
    """

    width: float
    h_align: HAlign = HAlign.CENTER

    def __post_init__(self) -> None:
        """Validate the column width.

        Raises:
            ValueError: On a non-positive width.
        """
        if self.width <= 0:
            raise ValueError(f"column width must be > 0 (here: {self.width}).")

    @classmethod
    def multi(cls, n: int, width: float, h_align: HAlign = HAlign.CENTER) -> tuple[TableColumn, ...]:
        """Declare n identical-looking but distinct columns in one call.

        Raises:
            ValueError: On n < 1.
        """
        if n < 1:
            raise ValueError(f"n must be >= 1 (here: {n}).")
        return tuple(cls(width=width, h_align=h_align) for _ in range(n))


# ==================================================================================================
#  PlottingColumn
# ==================================================================================================
@dataclass(frozen=True, eq=False)
class PlottingColumn(TableColumn):
    """A column that is itself a plot: carries the data axis for its x direction.

    Behavior lives with the data — but the column is still a spec, not an
    Element: geometry stays the hosting table's job.
    """

    axis: PlotAxis = field(kw_only=True)


# ==================================================================================================
#  ColumnGroup
# ==================================================================================================
@dataclass(frozen=True)
class ColumnGroup:
    """An ordered set of columns sharing major grid boundaries."""

    columns: tuple[TableColumn, ...]
    name: str = ""

    def __post_init__(self) -> None:
        """Validate the group contents.

        Raises:
            ValueError: On an empty group.
        """
        if not self.columns:
            raise ValueError("a ColumnGroup requires at least one column.")
