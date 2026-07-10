"""Matplotlib wrapper for composite figure building."""

from .axis import PlotAxis, ScaleLinear, ScaleLinLog, ScaleLog, Ticks
from .elements import Composite, Spacer, Text
from .figure import CompositeFigure, save_figure
from .geometry import HAlign, Margin, Range, VAlign
from .plot import Legend, LegendEntry, PlotAxes
from .style import ColorRange, FontWeight, LineStyle, TextStyle, Theme
from .table import ColumnGroup, PlottingColumn, Table, TableColumn, TableLayout

__all__ = [
    "ColorRange",
    "ColumnGroup",
    "Composite",
    "CompositeFigure",
    "FontWeight",
    "HAlign",
    "Legend",
    "LegendEntry",
    "LineStyle",
    "Margin",
    "PlotAxes",
    "PlotAxis",
    "PlottingColumn",
    "Range",
    "ScaleLinLog",
    "ScaleLinear",
    "ScaleLog",
    "Spacer",
    "Table",
    "TableColumn",
    "TableLayout",
    "Text",
    "TextStyle",
    "Theme",
    "Ticks",
    "VAlign",
    "save_figure",
]
