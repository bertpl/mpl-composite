"""The single shared style vocabulary, specialized per element via modify()."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ._line_style import LineStyle
from ._text_style import FontWeight, TextStyle


@dataclass(frozen=True)
class Theme:
    """One shared style vocabulary for all element families.

    Elements take a Theme as a constructor argument and read named styles from
    it; specializations are made with modify() rather than per-subsystem
    constants classes.
    """

    # --- lines ---
    border_major: LineStyle = LineStyle(color=(0.0, 0.0, 0.0), width=1.0)
    border_minor: LineStyle = LineStyle(color=(0.5, 0.5, 0.5), width=0.5)
    grid_major: LineStyle = LineStyle(color=(0.8, 0.8, 0.8), width=0.5)
    grid_minor: LineStyle = LineStyle(color=(0.9, 0.9, 0.9), width=0.35)
    tick: LineStyle = LineStyle(color=(0.0, 0.0, 0.0), width=0.75)

    # --- text ---
    text: TextStyle = TextStyle(size=10.0)
    text_title: TextStyle = TextStyle(size=14.0, weight=FontWeight.BOLD)
    text_tick_label: TextStyle = TextStyle(size=8.0)

    # --- colors ---
    band_color: tuple[float, float, float] = (0.97, 0.97, 0.97)

    def modify(self, **overrides: object) -> Theme:
        """Copy with the given fields replaced (dataclasses.replace semantics)."""
        return dataclasses.replace(self, **overrides)  # type: ignore[arg-type]


DEFAULT_THEME = Theme()
