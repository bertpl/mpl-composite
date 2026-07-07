"""Tick value objects and the raw tick-generation algorithms."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

# Relative tolerance for "is this multiple still inside the range" decisions, so
# ranges with slightly ugly bounds (0.999999...) do not drop their edge ticks.
_REL_EPS = 1e-9


def _default_fmt(v: float) -> str:
    """Default tick-label formatting: compact general format ('%g')."""
    return f"{v:g}"


# ==================================================================================================
#  Ticks
# ==================================================================================================
@dataclass(frozen=True)
class Ticks:
    """Minor/major tick positions with their labels (parallel tuples).

    Positions listed as major are dropped from the minor tuples at
    construction, so the two sets are always disjoint.
    """

    major: tuple[float, ...]
    major_labels: tuple[str, ...]
    minor: tuple[float, ...] = field(default=())
    minor_labels: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        """Validate parallel lengths and drop minors that duplicate a major position."""
        if len(self.major) != len(self.major_labels):
            raise ValueError(f"major and major_labels must be parallel ({len(self.major)} vs {len(self.major_labels)}).")
        if len(self.minor) != len(self.minor_labels):
            raise ValueError(f"minor and minor_labels must be parallel ({len(self.minor)} vs {len(self.minor_labels)}).")

        filtered = [
            (position, label)
            for position, label in zip(self.minor, self.minor_labels, strict=True)
            if not any(math.isclose(position, major, rel_tol=_REL_EPS, abs_tol=0.0) for major in self.major)
        ]
        object.__setattr__(self, "minor", tuple(position for position, _ in filtered))
        object.__setattr__(self, "minor_labels", tuple(label for _, label in filtered))

    @property
    def positions(self) -> tuple[float, ...]:
        """All tick positions (major + minor), sorted."""
        return tuple(sorted(set(self.major) | set(self.minor)))

    @classmethod
    def from_values(
        cls,
        major: Sequence[float],
        minor: Sequence[float] = (),
        fmt: Callable[[float], str] = _default_fmt,
    ) -> Ticks:
        """Construct Ticks from bare positions, generating labels with `fmt`."""
        return cls(
            major=tuple(major),
            major_labels=tuple(fmt(v) for v in major),
            minor=tuple(minor),
            minor_labels=tuple(fmt(v) for v in minor),
        )


# ==================================================================================================
#  Raw algorithms
# ==================================================================================================
def _multiple_indices(v_min: float, v_max: float, step: float) -> range:
    """Integer multiples i of `step` with i*step inside [v_min, v_max], edge-tolerant."""
    eps = _REL_EPS * max(1.0, abs(v_min), abs(v_max))
    return range(math.ceil((v_min - eps) / step), math.floor((v_max + eps) / step) + 1)


def linear_ticks(
    v_min: float,
    v_max: float,
    *,
    n_major_target: int = 5,
    n_minor_per_major: int = 4,
    fmt: Callable[[float], str] | None = None,
) -> Ticks:
    """Generate 'nice' linear ticks covering [v_min, v_max].

    Major ticks sit at multiples of a step chosen from {1, 2, 2.5, 5} x 10^k,
    picking the candidate whose in-range tick count lands nearest
    `n_major_target` (ties go to the larger step — a calmer axis). Minor ticks
    subdivide the major step and run to the range edges. Ugly, non-round bounds
    are tolerated: ticks simply start at the first in-range multiple.

    Args:
        v_min: Lower bound of the value range; must be < v_max.
        v_max: Upper bound of the value range.
        n_major_target: Desired number of major ticks (a target, not a promise).
        n_minor_per_major: Minor ticks between two consecutive majors.
        fmt: Tick-label formatter; defaults to compact '%g' formatting.

    Raises:
        ValueError: On an empty or inverted range.
    """
    if not v_max > v_min:
        raise ValueError(f"linear_ticks requires v_min < v_max (here: {v_min}, {v_max}).")
    fmt = fmt or _default_fmt

    # --- choose the major step --------------------------
    k0 = math.floor(math.log10(v_max - v_min))
    candidates = sorted((m * 10.0**k for k in (k0 - 2, k0 - 1, k0, k0 + 1) for m in (1.0, 2.0, 2.5, 5.0)), reverse=True)
    best_step, best_score = None, None
    for step in candidates:  # descending: ties resolve to the larger step
        n = len(_multiple_indices(v_min, v_max, step))
        if n < 2:
            continue
        score = abs(n - n_major_target)
        if best_score is None or score < best_score:
            best_step, best_score = step, score
    if best_step is None:  # pragma: no cover - smallest candidate always yields >= 2 ticks
        raise AssertionError("unreachable: no viable step candidate")

    # --- major & minor positions ------------------------
    major = [i * best_step for i in _multiple_indices(v_min, v_max, best_step)]
    minor_step = best_step / (n_minor_per_major + 1)
    n_sub = n_minor_per_major + 1
    minor = [i * minor_step for i in _multiple_indices(v_min, v_max, minor_step) if i % n_sub != 0]

    return Ticks(
        major=tuple(major),
        major_labels=tuple(fmt(v) for v in major),
        minor=tuple(minor),
        minor_labels=tuple(fmt(v) for v in minor),
    )


def log_ticks(
    v_min: float,
    v_max: float,
    *,
    base: float = 10.0,
    minor_subs: Sequence[float] = (2.0, 5.0),
    fmt: Callable[[float], str] | None = None,
) -> Ticks:
    """Generate logarithmic ticks covering [v_min, v_max].

    Major ticks sit at integer powers of `base`; minor ticks at `minor_subs`
    multiples of each power. A range containing fewer than two base powers
    (sub-decade) falls back to linear_ticks — powers alone cannot carry such an
    axis.

    Args:
        v_min: Lower bound of the value range; must be > 0 and < v_max.
        v_max: Upper bound of the value range.
        base: Logarithm base; must be > 1.
        minor_subs: Sub-multiples used for minor ticks, each in (1, base).
        fmt: Tick-label formatter; defaults to compact '%g' formatting.

    Raises:
        ValueError: On a non-positive/inverted range, base <= 1, or a
            minor sub outside (1, base).
    """
    if not 0 < v_min < v_max:
        raise ValueError(f"log_ticks requires 0 < v_min < v_max (here: {v_min}, {v_max}).")
    if base <= 1:
        raise ValueError(f"log_ticks requires base > 1 (here: {base}).")
    if any(not 1 < sub < base for sub in minor_subs):
        raise ValueError(f"minor_subs must each lie strictly inside (1, base) (here: {tuple(minor_subs)}).")
    fmt = fmt or _default_fmt

    # --- major positions: integer powers of base ---------
    k_first = math.ceil(math.log(v_min, base) - _REL_EPS)
    k_last = math.floor(math.log(v_max, base) + _REL_EPS)
    major = [base**k for k in range(k_first, k_last + 1)]
    if len(major) < 2:
        return linear_ticks(v_min, v_max, fmt=fmt)  # sub-decade fallback

    # --- minor positions: subs per decade, to the edges --
    eps = _REL_EPS * max(1.0, abs(v_max))
    minor = sorted(
        sub * base**k
        for k in range(k_first - 1, k_last + 1)
        for sub in minor_subs
        if (v_min - eps) <= sub * base**k <= (v_max + eps)
    )

    return Ticks(
        major=tuple(major),
        major_labels=tuple(fmt(v) for v in major),
        minor=tuple(minor),
        minor_labels=tuple(fmt(v) for v in minor),
    )
