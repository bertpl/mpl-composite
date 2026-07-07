"""The legend element: swatch + label rows in a measured n-column grid."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from mpl_composite.canvas import artist_size
from mpl_composite.elements import Element
from mpl_composite.geometry import XYZ, HAlign
from mpl_composite.style import DEFAULT_THEME

if TYPE_CHECKING:
    from collections.abc import Sequence

    from mpl_composite.canvas import Canvas
    from mpl_composite.elements import Layout
    from mpl_composite.style import LineStyle, TextStyle, Theme

# Internal geometry, as fractions of the row height.
_PAD = 0.35  # padding between the frame and the content
_SAMPLE_GAP = 0.25  # gap between a swatch and its label
_COL_GAP = 0.75  # gap between columns
_TEXT_FILL = 0.6  # label text height


# ==================================================================================================
#  Text aspect measurement
# ==================================================================================================
_MEASURE_FIG: Figure | None = None


def _text_aspect(s: str, style: TextStyle) -> float:
    """Width-over-height of a rendered string — unit-free, measured on a private Agg renderer.

    Measured before any element canvas exists (Legend sizes itself in
    measure(), which precedes placement), so a throwaway figure stands in for
    the real renderer; the ratio is what matters and carries across figures.
    """
    global _MEASURE_FIG  # noqa: PLW0603 - lazily built, then reused as a pure measurement device
    if _MEASURE_FIG is None:
        _MEASURE_FIG = Figure()
        FigureCanvasAgg(_MEASURE_FIG)
        _MEASURE_FIG.add_subplot()
    ax = _MEASURE_FIG.axes[0]
    artist = ax.text(0, 0, s, fontsize=style.size, fontweight=style.weight.value, rotation=style.rotation_deg)
    width, height = artist_size(_MEASURE_FIG, ax, artist)
    artist.remove()
    return width / height


# ==================================================================================================
#  LegendEntry
# ==================================================================================================
@dataclass(frozen=True)
class LegendEntry:
    """One legend row: a line-style swatch plus its label."""

    label: str
    style: LineStyle


# ==================================================================================================
#  Legend
# ==================================================================================================
class Legend(Element):
    """Multi-column legend with measured text widths and plain anchoring.

    A regular element: place it in any composite cell (alignment and margins
    do the anchoring), or add it on top of a plot area inside a PlotAxes
    subclass. Entries fill the grid in reading order; column widths follow
    the widest label per column. Fonts auto-scale to the row height.
    """

    def __init__(
        self,
        entries: Sequence[LegendEntry],
        *,
        n_cols: int = 1,
        row_height: float = 0.05,
        sample_width: float = 0.04,
        frame: bool = True,
        text_style: TextStyle | None = None,
        theme: Theme = DEFAULT_THEME,
    ) -> None:
        """Declare the entries and the legend geometry.

        Args:
            entries: The legend rows, in reading order.
            n_cols: Number of columns the entries flow into.
            row_height: Height of one entry row, in layout units — the size
                knob everything else scales with.
            sample_width: Width of the line-sample swatch, in layout units.
            frame: Whether to draw a framed white background.
            text_style: Label style; size acts as the measurement reference
                (drawn size fits the row). Defaults to the theme's text style.
            theme: Style vocabulary for the frame and default text.

        Raises:
            ValueError: On no entries or a non-positive n_cols/row_height.
        """
        if not entries:
            raise ValueError("Legend requires at least one entry.")
        if n_cols < 1:
            raise ValueError(f"n_cols must be >= 1 (here: {n_cols}).")
        if row_height <= 0:
            raise ValueError(f"row_height must be > 0 (here: {row_height}).")
        self._entries = list(entries)
        self._n_cols = min(n_cols, len(self._entries))
        self._row_height = row_height
        self._sample_width = sample_width
        self._frame = frame
        self._text_style = text_style if text_style is not None else theme.text
        self._theme = theme

    # --------------------------------------------------------------------------
    #  Geometry
    # --------------------------------------------------------------------------
    @property
    def _n_rows(self) -> int:
        """Rows needed to fit all entries in the column count."""
        return -(-len(self._entries) // self._n_cols)

    def _column_widths(self) -> list[float]:
        """Per-column width: swatch + gap + the column's widest label."""
        text_height = _TEXT_FILL * self._row_height
        widths = []
        for j in range(self._n_cols):
            labels = [entry.label for entry in self._entries[j :: self._n_cols]]
            text_width = max(_text_aspect(label, self._text_style) * text_height for label in labels)
            widths.append(self._sample_width + _SAMPLE_GAP * self._row_height + text_width)
        return widths

    def measure(self) -> XYZ:
        """Padded grid size, with a unit z extent for background/content layering."""
        pad = _PAD * self._row_height
        width = 2 * pad + sum(self._column_widths()) + (self._n_cols - 1) * _COL_GAP * self._row_height
        height = 2 * pad + self._n_rows * self._row_height
        return XYZ(width, height, 1.0)

    # --------------------------------------------------------------------------
    #  Drawing
    # --------------------------------------------------------------------------
    def draw(self, layout: Layout) -> None:
        """Framed background (optional), then per-entry swatch + label."""
        canvas = layout.canvas

        # --- background & frame ---------------------------
        if self._frame:
            canvas.rectangle(
                canvas.x.min,
                canvas.x.max,
                canvas.y.min,
                canvas.y.max,
                fill_color=(1.0, 1.0, 1.0),
                edge_style=self._theme.border_minor,
                zorder=0.05,
            )

        # --- entries --------------------------------------
        pad = _PAD * self._row_height
        column_widths = self._column_widths()
        for i, entry in enumerate(self._entries):
            i_row, i_col = divmod(i, self._n_cols)
            x = canvas.x.min + pad + sum(column_widths[:i_col]) + i_col * _COL_GAP * self._row_height
            y = canvas.y.max - pad - (i_row + 0.5) * self._row_height

            canvas.plot_sample(x, x + self._sample_width, y, entry.style.modify(zorder=0.5))

            style = self._text_style.modify(size=self._label_font_size(canvas, entry.label))
            canvas.text(
                x + self._sample_width + _SAMPLE_GAP * self._row_height,
                y,
                entry.label,
                style,
                h_align=HAlign.LEFT,
                zorder=0.5,
            )

    def _label_font_size(self, canvas: Canvas, label: str) -> float:
        """Font size that renders the label at the row's text height on this canvas."""
        _, height_ref = canvas.text_size(label, self._text_style)
        return self._text_style.size * (_TEXT_FILL * self._row_height) / height_ref
