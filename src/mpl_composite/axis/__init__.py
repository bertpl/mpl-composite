"""Data axes: value ranges, scales, ticks, and the immutable PlotAxis."""

from ._plot_axis import PlotAxis
from ._scale import Scale, ScaleLinear, ScaleLinLog, ScaleLog
from ._ticks import Ticks, linear_ticks, log_ticks

__all__ = ["PlotAxis", "Scale", "ScaleLinLog", "ScaleLinear", "ScaleLog", "Ticks", "linear_ticks", "log_ticks"]
