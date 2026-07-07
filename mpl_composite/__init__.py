"""Matplotlib wrapper for composite figure building."""

from .axis import PlotAxis, ScaleLinear, ScaleLinLog, ScaleLog, Ticks
from .geometry import HAlign, Margin, Range, VAlign
from .style import ColorRange, FontWeight, LineStyle, TextStyle, Theme

__all__ = [
    "ColorRange",
    "FontWeight",
    "HAlign",
    "LineStyle",
    "Margin",
    "PlotAxis",
    "Range",
    "ScaleLinLog",
    "ScaleLinear",
    "ScaleLog",
    "TextStyle",
    "Theme",
    "Ticks",
    "VAlign",
]
