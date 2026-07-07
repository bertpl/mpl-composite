"""Vectorized, invertible 1-D mappings from plot coordinates to axis coordinates."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

import numpy as np

from mpl_composite.geometry import Range


# ==================================================================================================
#  Transform (base class)
# ==================================================================================================
class Transform(ABC):
    """Invertible 1-D mapping from plot coordinates to axis coordinates.

    Vectorized: `__call__` and `inv` accept a float, list of floats, or numpy
    array and return the same type. `reverse=True` flips orientation within the
    axis range (used e.g. for top-down y-axes).

    Degenerate ranges are mapped robustly: a zero-size plot range maps every
    value to the axis-range center, and the corresponding inverse returns the
    plot-range center.
    """

    def __init__(self, plot_range: Range, ax_range: Range, reverse: bool = False) -> None:
        """Bind the mapping to its plot- and axis-coordinate ranges.

        Args:
            plot_range: Input range, in plot coordinates.
            ax_range: Output range, in axis coordinates.
            reverse: If True, flip orientation (plot min maps to axis max).
        """
        self._plot_range = plot_range
        self._ax_range = ax_range
        self._reverse = reverse

    # --------------------------------------------------------------------------
    #  Properties
    # --------------------------------------------------------------------------
    @property
    def plot_range(self) -> Range:
        """Input range, in plot coordinates."""
        return self._plot_range

    @property
    def ax_range(self) -> Range:
        """Output range, in axis coordinates."""
        return self._ax_range

    @property
    def is_reverse(self) -> bool:
        """Whether the transform flips orientation."""
        return self._reverse

    # --------------------------------------------------------------------------
    #  Main API
    # --------------------------------------------------------------------------
    def __call__(self, v: float | list[float] | np.ndarray) -> float | list[float] | np.ndarray:
        """Forward transform (plot -> axis), preserving the input type."""
        is_scalar = isinstance(v, int | float)
        is_list = isinstance(v, list)

        v_arr = np.asarray([v] if is_scalar else v, dtype=float)
        result = self._forward(v_arr)
        if self._reverse:
            result = self._ax_range.max - (result - self._ax_range.min)

        if is_scalar:
            return float(result[0])
        if is_list:
            return [float(el) for el in result]
        return result

    def inv(self, v: float | list[float] | np.ndarray) -> float | list[float] | np.ndarray:
        """Backward transform (axis -> plot), preserving the input type."""
        is_scalar = isinstance(v, int | float)
        is_list = isinstance(v, list)

        v_arr = np.asarray([v] if is_scalar else v, dtype=float)
        if self._reverse:
            v_arr = self._ax_range.max - (v_arr - self._ax_range.min)
        result = self._backward(v_arr)

        if is_scalar:
            return float(result[0])
        if is_list:
            return [float(el) for el in result]
        return result

    def map_range(self, r: Range) -> Range:
        """Transform a plot-coordinate Range to an axis-coordinate Range (orientation-safe)."""
        endpoints = self._forward(np.asarray([r.min, r.max], dtype=float))
        if self._reverse:
            endpoints = self._ax_range.max - (endpoints - self._ax_range.min)
        return Range(float(endpoints.min()), float(endpoints.max()))

    # --------------------------------------------------------------------------
    #  Abstract API
    # --------------------------------------------------------------------------
    @abstractmethod
    def _forward(self, v: np.ndarray) -> np.ndarray:
        """Forward transform (plot -> axis), irrespective of the reverse flag."""

    @abstractmethod
    def _backward(self, v: np.ndarray) -> np.ndarray:
        """Backward transform (axis -> plot), irrespective of the reverse flag."""

    @abstractmethod
    def is_linear(self) -> bool:
        """True when the mapping is position-independent (deltas transform uniformly).

        Consulted by delta-based Canvas operations as a validity guard, not for
        behavioral branching — scale-dependent behavior belongs in Transform and
        Scale polymorphism.
        """

    # --------------------------------------------------------------------------
    #  Factory methods
    # --------------------------------------------------------------------------
    @classmethod
    def linear(cls, plot_range: Range, ax_range: Range, reverse: bool = False) -> TransformLinear:
        """Construct a linear transform."""
        return TransformLinear(plot_range, ax_range, reverse)

    @classmethod
    def log(cls, plot_range: Range, ax_range: Range, reverse: bool = False) -> TransformLog:
        """Construct a logarithmic transform."""
        return TransformLog(plot_range, ax_range, reverse)

    @classmethod
    def lin_log(
        cls,
        plot_range: Range,
        ax_range: Range,
        plot_lin_max: float,
        ax_lin_fraction: float,
        reverse: bool = False,
    ) -> TransformLinLog:
        """Construct a lin-log transform (linear below plot_lin_max, logarithmic above)."""
        return TransformLinLog(plot_range, ax_range, plot_lin_max, ax_lin_fraction, reverse)


# ==================================================================================================
#  TransformLinear
# ==================================================================================================
class TransformLinear(Transform):
    """Affine mapping with precomputed forward/backward coefficients."""

    def __init__(self, plot_range: Range, ax_range: Range, reverse: bool = False) -> None:
        """See Transform.__init__ for the argument contract."""
        super().__init__(plot_range, ax_range, reverse)

        # forward:  v_ax = c0 + c1 * v_plot   (degenerate plot range -> constant map)
        if plot_range.size == 0:
            self._c0, self._c1 = ax_range.center, 0.0
        else:
            self._c1 = ax_range.size / plot_range.size
            self._c0 = ax_range.min - (plot_range.min * self._c1)

        # backward: v_plot = c0_inv + c1_inv * v_ax   (degenerate either way -> constant map)
        if self._c1 == 0.0:
            self._c0_inv, self._c1_inv = plot_range.center, 0.0
        else:
            self._c1_inv = 1.0 / self._c1
            self._c0_inv = plot_range.min - (ax_range.min * self._c1_inv)

    def _forward(self, v: np.ndarray) -> np.ndarray:
        return self._c0 + (self._c1 * v)

    def _backward(self, v: np.ndarray) -> np.ndarray:
        return self._c0_inv + (self._c1_inv * v)

    def is_linear(self) -> bool:
        """Linear by definition."""
        return True


# ==================================================================================================
#  TransformLog
# ==================================================================================================
class TransformLog(Transform):
    """Logarithmic mapping: equal plot-value ratios map to equal axis-coordinate distances."""

    def __init__(self, plot_range: Range, ax_range: Range, reverse: bool = False) -> None:
        """See Transform.__init__; additionally requires a strictly positive plot range.

        Raises:
            ValueError: If plot_range.min <= 0 (log of non-positive values).
        """
        super().__init__(plot_range, ax_range, reverse)
        if plot_range.min <= 0:
            raise ValueError(f"TransformLog requires a strictly positive plot range (here: {plot_range}).")

        # forward:  v_ax = c0 + c1 * ln(v_plot)   (degenerate plot range -> constant map)
        log_size = math.log(plot_range.max) - math.log(plot_range.min)
        if log_size == 0:
            self._c0, self._c1 = ax_range.center, 0.0
        else:
            self._c1 = ax_range.size / log_size
            self._c0 = ax_range.min - (math.log(plot_range.min) * self._c1)

        # backward: ln(v_plot) = c0_inv + c1_inv * v_ax   (degenerate either way -> constant map)
        if self._c1 == 0.0:
            self._c0_inv, self._c1_inv = math.log(plot_range.center), 0.0
        else:
            self._c1_inv = 1.0 / self._c1
            self._c0_inv = math.log(plot_range.min) - (ax_range.min * self._c1_inv)

    def _forward(self, v: np.ndarray) -> np.ndarray:
        return self._c0 + (self._c1 * np.log(v))

    def _backward(self, v: np.ndarray) -> np.ndarray:
        return np.exp(self._c0_inv + (self._c1_inv * v))

    def is_linear(self) -> bool:
        """Non-linear by definition."""
        return False


# ==================================================================================================
#  TransformLinLog
# ==================================================================================================
class TransformLinLog(Transform):
    """Combined linear-logarithmic mapping.

    The lower part of the plot range maps linearly, the upper part
    logarithmically:

        [plot_min, plot_lin_max]  --linear-->  [ax_min, ax_lin_max]
        [plot_lin_max, plot_max]  --log----->  [ax_lin_max, ax_max]

    with ax_lin_max sitting at `ax_lin_fraction` of the axis range. Useful for
    axes that must show 0 (or negative values) and still span decades.
    """

    def __init__(
        self,
        plot_range: Range,
        ax_range: Range,
        plot_lin_max: float,
        ax_lin_fraction: float,
        reverse: bool = False,
    ) -> None:
        """See Transform.__init__ for the shared arguments.

        Args:
            plot_range: Input range, in plot coordinates.
            ax_range: Output range, in axis coordinates.
            plot_lin_max: Plot value where the mapping switches to logarithmic;
                must lie strictly inside plot_range and be strictly positive.
            ax_lin_fraction: Fraction of the axis extent given to the linear
                part; must lie strictly inside (0, 1).
            reverse: If True, flip orientation.

        Raises:
            ValueError: On a switch point outside the plot range, a
                non-positive switch point, or a fraction outside (0, 1).
        """
        super().__init__(plot_range, ax_range, reverse)
        if not (plot_range.min < plot_lin_max < plot_range.max):
            raise ValueError(f"plot_lin_max must lie strictly inside {plot_range} (here: {plot_lin_max}).")
        if plot_lin_max <= 0:
            raise ValueError(f"plot_lin_max must be strictly positive (here: {plot_lin_max}).")
        if not (0.0 < ax_lin_fraction < 1.0):
            raise ValueError(f"ax_lin_fraction must lie strictly inside (0, 1) (here: {ax_lin_fraction}).")

        self._plot_lin_max = plot_lin_max
        ax_lin_max = ax_range.at(ax_lin_fraction)
        self._lin = TransformLinear(Range(plot_range.min, plot_lin_max), Range(ax_range.min, ax_lin_max))
        self._log = TransformLog(Range(plot_lin_max, plot_range.max), Range(ax_lin_max, ax_range.max))

    def _forward(self, v: np.ndarray) -> np.ndarray:
        result = np.empty(v.shape, dtype=float)
        mask = v <= self._plot_lin_max
        result[mask] = self._lin._forward(v[mask])  # noqa: SLF001  (same class family)
        result[~mask] = self._log._forward(v[~mask])  # noqa: SLF001
        return result

    def _backward(self, v: np.ndarray) -> np.ndarray:
        ax_lin_max = self._lin.ax_range.max
        result = np.empty(v.shape, dtype=float)
        mask = v <= ax_lin_max
        result[mask] = self._lin._backward(v[mask])  # noqa: SLF001
        result[~mask] = self._log._backward(v[~mask])  # noqa: SLF001
        return result

    def is_linear(self) -> bool:
        """Non-linear by definition."""
        return False
