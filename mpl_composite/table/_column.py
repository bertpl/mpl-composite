"""Declarative column specs: pure data describing table columns and their grouping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from mpl_composite.geometry import HAlign, VAlign

if TYPE_CHECKING:
    from mpl_composite.axis import PlotAxis
    from mpl_composite.canvas import Canvas
    from mpl_composite.style import Theme

# Angle of skewed labels (tick labels below a plotting column, skewed column names).
LABEL_ANGLE_DEG = 60.0

# Decoration geometry below the data rows, in row heights.
_TICK_LENGTH_MAJOR = 0.20
_TICK_LENGTH_MINOR = 0.15
_TICK_LABEL_GAP = 0.02  # between a tick mark's end and its label
_AXIS_LABEL_DROP = 1.5  # from the data band's bottom edge to the axis label
_MINOR_LABEL_SCALE = 0.75  # minor tick-label size, relative to the major labels

# Local z levels on the column's data canvas (its z range is (0, 1)): the grid
# hugs the bottom so content at the LineStyle default of 0 lands on grid level;
# ticks and labels sit on top of ordinary content.
_Z_GRID_MINOR = 0.01
_Z_GRID_MAJOR = 0.02
_Z_TICKS = 0.9


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
    Element: geometry stays the hosting table's job. The hosting table builds
    the column's data-coordinate canvas (TableLayout.column_canvas); this class
    only knows how to draw its own plot furniture on it.
    """

    axis: PlotAxis = field(kw_only=True)

    def draw_decorations(self, canvas: Canvas, theme: Theme) -> None:
        """Draw the column's plot furniture on its data-coordinate canvas.

        Vertical grid lines at the axis ticks, tick marks and skewed tick
        labels below the data rows, and the axis label below those (canvas y
        coordinates past the data rows extrapolate into the table's footer).
        """
        ticks = self.axis.ticks
        y_bottom = canvas.bottom  # the data band's bottom edge (top-down canvas)

        # --- grid -----------------------------------------
        canvas.vline(list(ticks.minor), theme.grid_minor.modify(zorder=_Z_GRID_MINOR))
        canvas.vline(list(ticks.major), theme.grid_major.modify(zorder=_Z_GRID_MAJOR))

        # --- tick marks & labels --------------------------
        tick = theme.tick.modify(zorder=_Z_TICKS)
        major_style = theme.text_tick_label.modify(rotation_deg=LABEL_ANGLE_DEG)
        minor_style = major_style.modify(size=_MINOR_LABEL_SCALE * major_style.size)
        for positions, labels, length, style in [
            (ticks.major, ticks.major_labels, _TICK_LENGTH_MAJOR, major_style),
            (ticks.minor, ticks.minor_labels, _TICK_LENGTH_MINOR, minor_style),
        ]:
            for position, label in zip(positions, labels, strict=True):
                canvas.vline(position, tick, y_min=y_bottom, y_max=y_bottom + length)
                if label:
                    canvas.text(
                        position,
                        y_bottom + length + _TICK_LABEL_GAP,
                        label,
                        style,
                        h_align=HAlign.RIGHT,
                        v_align=VAlign.TOP,
                        zorder=_Z_TICKS,
                    )

        # --- axis label -----------------------------------
        if self.axis.label:
            canvas.text(
                self.axis.mid_point,
                y_bottom + _AXIS_LABEL_DROP,
                self.axis.label,
                theme.text,
                h_align=HAlign.CENTER,
                v_align=VAlign.TOP,
                zorder=_Z_TICKS,
            )


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
