"""Matplotlib wrapper for composite figure building."""

from .axis import PlotAxis, ScaleLinear, ScaleLinLog, ScaleLog, Ticks
from .elements import Composite, Spacer, Text
from .figure import CompositeFigure, save_figure
from .geometry import HAlign, Margin, Range, VAlign
from .plot import Legend, LegendEntry, PlotAxes
from .style import ColorRange, FontWeight, LineStyle, TextStyle, Theme

__all__ = [
    "ColorRange",
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
    "Range",
    "ScaleLinLog",
    "ScaleLinear",
    "ScaleLog",
    "Spacer",
    "Text",
    "TextStyle",
    "Theme",
    "Ticks",
    "VAlign",
    "save_figure",
]
