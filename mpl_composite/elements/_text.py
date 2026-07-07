"""A text box element that auto-scales its font to fill its declared box."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mpl_composite.geometry import XYZ, HAlign, VAlign
from mpl_composite.style import TextStyle

from ._element import Element

if TYPE_CHECKING:
    from mpl_composite.canvas import Canvas

    from ._layout import Layout

_DEFAULT_TEXT_STYLE = TextStyle()


class Text(Element):
    """A text box: auto-scales its font to fill the declared box, honoring alignment.

    The style's size acts as the measurement reference; the drawn size is
    whatever fills `fill_fraction` of the box.
    """

    def __init__(
        self,
        x_size: float,
        y_size: float,
        text: str,
        *,
        style: TextStyle = _DEFAULT_TEXT_STYLE,
        h_align: HAlign = HAlign.CENTER,
        v_align: VAlign = VAlign.CENTER,
        fill_fraction: float = 0.9,
    ) -> None:
        """Declare the box, its content, and how the text sits inside it.

        Raises:
            ValueError: On a non-positive box or a fill_fraction outside (0, 1].
        """
        if x_size <= 0 or y_size <= 0:
            raise ValueError(f"Text box sizes must be > 0 (here: ({x_size}, {y_size})).")
        if not 0.0 < fill_fraction <= 1.0:
            raise ValueError(f"fill_fraction must lie in (0, 1] (here: {fill_fraction}).")
        self._x_size = x_size
        self._y_size = y_size
        self._text = text
        self._style = style
        self._h_align = h_align
        self._v_align = v_align
        self._fill_fraction = fill_fraction

    def measure(self) -> XYZ:
        """The declared box; no z extent."""
        return XYZ(self._x_size, self._y_size, 0.0)

    def draw(self, layout: Layout) -> None:
        """Measure at the reference size, scale the font to fill the box, draw anchored."""
        if not self._text:
            return
        canvas = layout.canvas

        # --- auto-scale the font size --------------------
        w_ref, h_ref = canvas.text_size(self._text, self._style)
        scale = self._fill_fraction * min(self._x_size / w_ref, self._y_size / h_ref)
        style = self._style.modify(size=scale * self._style.size)

        # --- draw at the anchor point --------------------
        canvas.text(
            x=self._anchor_x(canvas),
            y=self._anchor_y(canvas),
            s=self._text,
            style=style,
            h_align=self._h_align,
            v_align=self._v_align,
        )

    # --------------------------------------------------------------------------
    #  Internal
    # --------------------------------------------------------------------------
    def _anchor_x(self, canvas: Canvas) -> float:
        """Plot x of the text anchor per the horizontal alignment."""
        if self._h_align is HAlign.LEFT:
            return canvas.left
        if self._h_align is HAlign.RIGHT:
            return canvas.right
        return canvas.x.center

    def _anchor_y(self, canvas: Canvas) -> float:
        """Plot y of the text anchor per the vertical alignment (orientation-safe)."""
        if self._v_align is VAlign.TOP:
            return canvas.top
        if self._v_align is VAlign.BOTTOM:
            return canvas.bottom
        return canvas.y.center
