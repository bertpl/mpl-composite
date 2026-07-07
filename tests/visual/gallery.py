"""The gallery of figures pinned by visual-regression baselines.

Every entry renders through the full measure -> place -> draw lifecycle; new
element families add a figure here so their visual output gets pinned.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from mpl_composite import (
    ColumnGroup,
    Composite,
    CompositeFigure,
    HAlign,
    Legend,
    LegendEntry,
    LineStyle,
    PlotAxes,
    PlotAxis,
    PlottingColumn,
    ScaleLinLog,
    ScaleLog,
    Spacer,
    Table,
    TableColumn,
    TableLayout,
    Text,
    TextStyle,
    VAlign,
)
from mpl_composite.geometry import Range, XYZRange
from mpl_composite.style import DEFAULT_THEME

if TYPE_CHECKING:
    from collections.abc import Callable

    from mpl_composite.canvas import Canvas


def demo_composite() -> CompositeFigure:
    """Title over a 2x2 inner grid with spacers: the v0.1.0 engine smoke figure."""
    fig = CompositeFigure(fig_inch_per_unit=4.0)
    fig.add(0, 0, Text(1.0, 0.15, "Demo title"))
    inner = Composite()
    inner.add(0, 0, Text(0.4, 0.1, "top left"))
    inner.add(0, 1, Spacer(0.1, 0.1))
    inner.add(1, 0, Spacer(0.1, 0.1))
    inner.add(1, 1, Text(0.4, 0.1, "bottom right"))
    fig.add(1, 0, inner, margin=0.05)
    return fig


_CURVE_STYLE = LineStyle(color=(0.2, 0.3, 0.8))
_SAMPLE_STYLE = LineStyle(color=(0.8, 0.3, 0.2), line_enabled=False, marker="o", marker_size=3.0)


class _ScatterDemo(PlotAxes):
    """Worked PlotAxes subclass: curves, scattered markers, an annotation, and a legend."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Assemble the plot and anchor a legend on top of its plot area."""
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        legend = Legend(
            [LegendEntry("power law", _CURVE_STYLE), LegendEntry("samples", _SAMPLE_STYLE)],
            row_height=0.04,
        )
        self.add(1, 1, legend, h_align=HAlign.RIGHT, v_align=VAlign.TOP, margin=0.015)

    def draw_plot(self, canvas: Canvas) -> None:
        """Two curves in data coordinates plus a pointed-out sample."""
        x = [0.5 + 0.05 * i for i in range(191)]
        canvas.plot(x, [10.0 * v**-1.5 for v in x], _CURVE_STYLE)
        canvas.plot(
            x[::10],
            [3.0 * math.exp(-((v - 5.0) ** 2)) + 0.1 for v in x[::10]],
            _SAMPLE_STYLE,
        )
        canvas.text(5.0, 3.5, "peak", TextStyle(size=8.0), zorder=0.5)


def plot_axes_demo() -> CompositeFigure:
    """A classic x/y plot: linear x, log y, title, axis labels, grid."""
    fig = CompositeFigure(fig_inch_per_unit=6.0)
    fig.add(
        0,
        0,
        _ScatterDemo(
            PlotAxis.from_range(0.5, 10.0, label="x value"),
            PlotAxis.from_range(0.05, 50.0, scale=ScaleLog(), label="y value"),
            plot_width=1.0,
            plot_height=0.7,
            title="Scatter demo",
        ),
        margin=0.02,
    )
    return fig


class _LinLogDemo(PlotAxes):
    """A curve rising from zero through several decades: the lin-log showcase."""

    def draw_plot(self, canvas: Canvas) -> None:
        """One quadratic-growth curve crossing the lin-log seam."""
        x = [0.05 * i for i in range(201)]
        canvas.plot(x, [v**3 for v in x], _CURVE_STYLE)


def linlog_plot_demo() -> CompositeFigure:
    """A classic plot with an automatic lin-log y axis (linear below 1, log above)."""
    fig = CompositeFigure(fig_inch_per_unit=6.0)
    fig.add(
        0,
        0,
        _LinLogDemo(
            PlotAxis.from_range(0.0, 10.0, label="x value"),
            PlotAxis.from_range(0.0, 1000.0, scale=ScaleLinLog(lin_max=1.0, lin_fraction=0.3), label="y value"),
            plot_width=1.0,
            plot_height=0.7,
            title="Lin-log demo",
        ),
        margin=0.02,
    )
    return fig


_RUNNERS = [
    ("1", "Ada Swift", "12.3", "24.9", "51.0"),
    ("2", "Bo Keita", "12.5", "25.1", "50.2"),
    ("3", "Cato Brandt", "12.4", "25.6", "52.3"),
    ("4", "Dee Okafor", "12.9", "25.8", "53.1"),
    ("5", "Eli Varga", "13.1", "26.2", "54.7"),
    ("6", "Fay Lindqvist", "13.0", "26.7", "55.0"),
]


class _RunnersTable(Table):
    """Worked Table subclass: a small race-results table with two column groups."""

    def __init__(self) -> None:
        """Declare the columns: a left-aligned identity group + three timing columns."""
        self._rank_col = TableColumn(width=0.05, h_align=HAlign.LEFT)
        self._name_col = TableColumn(width=0.25, h_align=HAlign.LEFT)
        self._time_cols = TableColumn.multi(3, width=0.11)
        super().__init__(
            n_rows=len(_RUNNERS),
            row_height=0.05,
            groups=(
                ColumnGroup(columns=(self._rank_col, self._name_col), name="runner"),
                ColumnGroup(columns=self._time_cols, name="splits"),
            ),
            cell_margin=0.01,
            header_rows=1.0,
            footer_rows=0.5,
        )

    def draw_content(self, table: TableLayout) -> None:
        """Column titles plus one text cell per (row, column)."""
        table.col_title(self._rank_col, "#")
        table.col_title(self._name_col, "name")
        for col, title in zip(self._time_cols, ["100m", "200m", "400m"], strict=True):
            table.col_title(col, title)
        for i_row, row in enumerate(_RUNNERS):
            for col, value in zip([self._rank_col, self._name_col, *self._time_cols], row, strict=True):
                table.cell_text(i_row, col, value)


def table_demo() -> CompositeFigure:
    """A banded table with grouped columns, titles, and per-cell text."""
    fig = CompositeFigure(fig_inch_per_unit=8.0)
    fig.add(0, 0, _RunnersTable(), margin=0.03)
    return fig


# (name, properties •/blank, difficulty, per-metric plot values) for the plotting-table demo.
_FUNCTIONS = [
    ("sphere", "• •  ", "0.8", (8.0, 6.5)),
    ("rosenbrock", " •  •", "2.4", (35.0, 28.0)),
    ("rastrigin", "•  • ", "3.1", (90.0, 70.0)),
    ("ackley", "•  ••", "2.2", (40.0, 45.0)),
    ("griewank", "•  • ", "1.9", (25.0, 21.0)),
    ("schwefel", "   • ", "3.6", (140.0, 110.0)),
    ("zakharov", "••   ", "1.1", (12.0, 13.5)),
    ("michalewicz", "   ••", "3.3", (65.0, 95.0)),
]
_PROPERTY_NAMES = ["separable", "convex", "multimodal", "shifted", "noisy"]
_MEAN_STYLE = LineStyle(color=(0.2, 0.3, 0.8), marker="o", marker_size=3.0)
_MEDIAN_STYLE = LineStyle(color=(0.8, 0.3, 0.2), style="--", marker="s", marker_size=3.0, marker_filled=False)
_TF_ROW_HEIGHT = 0.05  # layout units per table row; converts element sizes to row counts
_LEGEND_MARGIN = 0.015  # gap between the legend and the plot column's edges, in layout units


class _FunctionsTable(Table):
    """The table-family showcase: text groups, a skew-named property group, an embedded log plot."""

    def __init__(self) -> None:
        """Declare the column groups, ending in an embedded log-x plotting column."""
        self._rank_col = TableColumn(width=0.04, h_align=HAlign.LEFT)
        self._name_col = TableColumn(width=0.22, h_align=HAlign.LEFT)
        self._prop_cols = TableColumn.multi(len(_PROPERTY_NAMES), width=0.025)
        self._difficulty_col = TableColumn(width=0.10)
        self._plot_col = PlottingColumn(
            width=0.6, axis=PlotAxis.from_range(5.0, 200.0, scale=ScaleLog(), label="evaluations to convergence")
        )
        self._prop_group = ColumnGroup(columns=self._prop_cols, name="properties")
        super().__init__(
            n_rows=len(_FUNCTIONS),
            row_height=_TF_ROW_HEIGHT,
            groups=(
                ColumnGroup(columns=(self._rank_col, self._name_col), name="function"),
                self._prop_group,
                ColumnGroup(columns=(self._difficulty_col,), name="difficulty"),
                ColumnGroup(columns=(self._plot_col,), name="evaluations"),
            ),
            cell_margin=0.01,
            header_rows=1.5,
            footer_rows=4.0,
        )

    def draw_content(self, table: TableLayout) -> None:
        """Titles, cell text, skewed property names, and the embedded per-row metric plot."""
        # --- text columns ---------------------------------
        table.col_title(self._rank_col, "#")
        table.col_title(self._name_col, "function")
        table.col_title(self._difficulty_col, "difficulty")
        table.skewed_col_names(self._prop_group, _PROPERTY_NAMES)
        for i_row, (name, properties, difficulty, _) in enumerate(_FUNCTIONS):
            table.cell_text(i_row, self._rank_col, str(i_row + 1))
            table.cell_text(i_row, self._name_col, name)
            table.cell_text(i_row, self._difficulty_col, difficulty)
            for col, flag in zip(self._prop_cols, properties, strict=True):
                table.cell_text(i_row, col, flag.strip())

        # --- embedded plot column -------------------------
        canvas = table.column_canvas(self._plot_col)
        self._plot_col.draw_decorations(canvas, DEFAULT_THEME)
        for i_row, (_, _, _, (mean, median)) in enumerate(_FUNCTIONS):
            canvas.plot([mean / 1.4, mean, mean * 1.4], i_row - 0.18, _MEAN_STYLE)
            canvas.plot([median / 1.4, median, median * 1.4], i_row + 0.18, _MEDIAN_STYLE)
        self._draw_legend(table)

    def _draw_legend(self, table: TableLayout) -> None:
        """Anchor a legend inside the plot column's top-right corner.

        The legend element runs its own place -> draw on a sub-region of the
        table canvas, sized from its measurement (y converted to row units) and
        z-sliced above the plotted data.
        """
        legend = Legend([LegendEntry("mean", _MEAN_STYLE), LegendEntry("median", _MEDIAN_STYLE)], row_height=0.03)
        size = legend.measure()
        x_max = table.column_range(self._plot_col).max - _LEGEND_MARGIN
        y_top = _LEGEND_MARGIN / _TF_ROW_HEIGHT
        region = table.canvas.sub_region(
            XYZRange(
                x=Range(x_max - size.x, x_max),
                y=Range(y_top, y_top + size.y / _TF_ROW_HEIGHT),
                z=Range(0.85, 1.0),
            )
        )
        legend.draw(legend.place(region))


def plotting_table_demo() -> CompositeFigure:
    """The flagship figure: a table whose last column is a log-scale plot, with skewed labels."""
    fig = CompositeFigure(fig_inch_per_unit=8.0)
    fig.add(0, 0, _FunctionsTable(), margin=0.03)
    return fig


GALLERY: dict[str, Callable[[], CompositeFigure]] = {
    "demo_composite": demo_composite,
    "plot_axes_demo": plot_axes_demo,
    "linlog_plot_demo": linlog_plot_demo,
    "table_demo": table_demo,
    "plotting_table_demo": plotting_table_demo,
}
