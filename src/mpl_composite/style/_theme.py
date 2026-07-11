"""The single shared style vocabulary, specialized per element via modify()."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ._line_style import LineStyle
from ._text_style import FontWeight, TextStyle

# House defaults, as module constants: all style objects are frozen, so sharing
# one instance as a dataclass default is safe.
_DEFAULT_BORDER_MAJOR = LineStyle(color=(0.0, 0.0, 0.0), width=1.0)
_DEFAULT_BORDER_MINOR = LineStyle(color=(0.5, 0.5, 0.5), width=0.5)
_DEFAULT_GRID_MAJOR = LineStyle(color=(0.8, 0.8, 0.8), width=0.5)
_DEFAULT_GRID_MINOR = LineStyle(color=(0.9, 0.9, 0.9), width=0.35)
_DEFAULT_TICK = LineStyle(color=(0.0, 0.0, 0.0), width=0.75)
_DEFAULT_TEXT = TextStyle(size=10.0)
_DEFAULT_TEXT_TITLE = TextStyle(size=14.0, weight=FontWeight.BOLD)
_DEFAULT_TEXT_TICK_LABEL = TextStyle(size=8.0)


@dataclass(frozen=True)
class Theme:
    """One shared style vocabulary for all element families.

    Elements take a Theme as a constructor argument and read named styles from
    it; specializations are made with modify() rather than per-subsystem
    constants classes.
    """

    # --- lines ---
    border_major: LineStyle = _DEFAULT_BORDER_MAJOR
    border_minor: LineStyle = _DEFAULT_BORDER_MINOR
    grid_major: LineStyle = _DEFAULT_GRID_MAJOR
    grid_minor: LineStyle = _DEFAULT_GRID_MINOR
    tick: LineStyle = _DEFAULT_TICK

    # --- text ---
    text: TextStyle = _DEFAULT_TEXT
    text_title: TextStyle = _DEFAULT_TEXT_TITLE
    text_tick_label: TextStyle = _DEFAULT_TEXT_TICK_LABEL

    # --- colors ---
    band_color: tuple[float, float, float] = (0.97, 0.97, 0.97)

    def modify(self, **overrides: object) -> Theme:
        """Copy with the given fields replaced (dataclasses.replace semantics)."""
        return dataclasses.replace(self, **overrides)  # type: ignore[arg-type]


DEFAULT_THEME = Theme()
