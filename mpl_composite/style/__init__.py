"""Value objects for visual style: lines, text, colors, and the shared theme."""

from ._color_range import ColorRange
from ._line_style import LineStyle
from ._text_style import FontWeight, TextStyle
from ._theme import DEFAULT_THEME, Theme

__all__ = ["DEFAULT_THEME", "ColorRange", "FontWeight", "LineStyle", "TextStyle", "Theme"]
