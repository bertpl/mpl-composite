import pytest

from mpl_composite.axis import Ticks, linear_ticks, log_ticks


# ==================================================================================================
#  Ticks value object
# ==================================================================================================
def test_ticks_drops_minors_that_duplicate_majors() -> None:
    # --- act --------------------------
    ticks = Ticks(
        major=(0.0, 1.0),
        major_labels=("0", "1"),
        minor=(0.5, 1.0, 1.5),
        minor_labels=("0.5", "1", "1.5"),
    )

    # --- assert -----------------------
    assert ticks.minor == (0.5, 1.5)
    assert ticks.minor_labels == ("0.5", "1.5")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"major": (0.0, 1.0), "major_labels": ("0",)},
        {"major": (), "major_labels": (), "minor": (1.0,), "minor_labels": ()},
    ],
)
def test_ticks_rejects_non_parallel_labels(kwargs: dict) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="parallel"):
        Ticks(**kwargs)


def test_ticks_positions_sorted_union() -> None:
    # --- arrange ----------------------
    ticks = Ticks.from_values(major=[10.0, 1.0], minor=[5.0, 2.0])

    # --- act / assert -----------------
    assert ticks.positions == (1.0, 2.0, 5.0, 10.0)


def test_ticks_from_values_generates_labels() -> None:
    # --- act --------------------------
    ticks = Ticks.from_values(major=[0.0, 2.5, 1000.0])

    # --- assert -----------------------
    assert ticks.major_labels == ("0", "2.5", "1000")


def test_ticks_from_values_custom_fmt() -> None:
    # --- act --------------------------
    ticks = Ticks.from_values(major=[0.1, 0.2], fmt=lambda v: f"{v:.0%}")

    # --- assert -----------------------
    assert ticks.major_labels == ("10%", "20%")


# ==================================================================================================
#  linear_ticks — the settled nice-step table
# ==================================================================================================
@pytest.mark.parametrize(
    "v_min, v_max, n_major_target, expected_major",
    [
        # round ranges
        (0.0, 10.0, 5, (0.0, 2.5, 5.0, 7.5, 10.0)),
        (0.0, 1.0, 5, (0.0, 0.25, 0.5, 0.75, 1.0)),
        (0.0, 100.0, 5, (0.0, 25.0, 50.0, 75.0, 100.0)),
        # smaller target -> larger step
        (0.0, 10.0, 3, (0.0, 5.0, 10.0)),
        # ugly bounds: ticks start at the first in-range multiple
        (0.3, 9.7, 5, (2.0, 4.0, 6.0, 8.0)),
        # negative / zero-crossing ranges
        (-5.0, 5.0, 5, (-5.0, -2.5, 0.0, 2.5, 5.0)),
        (-1.0, 0.0, 5, (-1.0, -0.75, -0.5, -0.25, 0.0)),
        # large, non-round range
        (1234.0, 5678.0, 5, (2000.0, 3000.0, 4000.0, 5000.0)),
        # tiny magnitudes
        (0.0, 0.001, 5, (0.0, 0.00025, 0.0005, 0.00075, 0.001)),
    ],
)
def test_linear_ticks_major_positions(v_min: float, v_max: float, n_major_target: int, expected_major: tuple) -> None:
    # --- act --------------------------
    ticks = linear_ticks(v_min, v_max, n_major_target=n_major_target)

    # --- assert -----------------------
    assert ticks.major == pytest.approx(expected_major)


def test_linear_ticks_minor_positions() -> None:
    # --- act --------------------------
    ticks = linear_ticks(0.0, 10.0)  # majors at multiples of 2.5, minors subdivide by 5

    # --- assert -----------------------
    assert ticks.minor == pytest.approx(tuple(0.5 * i for i in range(21) if i % 5 != 0))


def test_linear_ticks_minor_subdivision_count() -> None:
    # --- act --------------------------
    ticks = linear_ticks(0.0, 10.0, n_major_target=3, n_minor_per_major=1)  # majors 0/5/10, minors halfway

    # --- assert -----------------------
    assert ticks.major == pytest.approx((0.0, 5.0, 10.0))
    assert ticks.minor == pytest.approx((2.5, 7.5))


def test_linear_ticks_labels_are_compact() -> None:
    # --- act --------------------------
    ticks = linear_ticks(0.0, 10.0)

    # --- assert -----------------------
    assert ticks.major_labels == ("0", "2.5", "5", "7.5", "10")


def test_linear_ticks_custom_fmt() -> None:
    # --- act --------------------------
    ticks = linear_ticks(0.0, 10.0, n_major_target=3, fmt=lambda v: f"{v:.1f}s")

    # --- assert -----------------------
    assert ticks.major_labels == ("0.0s", "5.0s", "10.0s")


def test_linear_ticks_rejects_empty_range() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="v_min < v_max"):
        linear_ticks(1.0, 1.0)


# ==================================================================================================
#  log_ticks
# ==================================================================================================
def test_log_ticks_decades_and_subs() -> None:
    # --- act --------------------------
    ticks = log_ticks(1.0, 1000.0)

    # --- assert -----------------------
    assert ticks.major == pytest.approx((1.0, 10.0, 100.0, 1000.0))
    assert ticks.minor == pytest.approx((2.0, 5.0, 20.0, 50.0, 200.0, 500.0))
    assert ticks.major_labels == ("1", "10", "100", "1000")


def test_log_ticks_non_power_bounds() -> None:
    # --- act --------------------------
    ticks = log_ticks(0.5, 200.0)

    # --- assert -----------------------
    assert ticks.major == pytest.approx((1.0, 10.0, 100.0))
    assert ticks.minor == pytest.approx((0.5, 2.0, 5.0, 20.0, 50.0, 200.0))


def test_log_ticks_sub_decade_falls_back_to_linear() -> None:
    # --- act --------------------------
    ticks = log_ticks(2.0, 8.0)

    # --- assert -----------------------
    assert ticks.major == linear_ticks(2.0, 8.0).major


def test_log_ticks_custom_base() -> None:
    # --- act --------------------------
    ticks = log_ticks(1.0, 16.0, base=2.0, minor_subs=(1.5,))

    # --- assert -----------------------
    assert ticks.major == pytest.approx((1.0, 2.0, 4.0, 8.0, 16.0))
    assert ticks.minor == pytest.approx((1.5, 3.0, 6.0, 12.0))


@pytest.mark.parametrize(
    "v_min, v_max, kwargs, match",
    [
        (0.0, 10.0, {}, "0 < v_min < v_max"),
        (-1.0, 10.0, {}, "0 < v_min < v_max"),
        (10.0, 1.0, {}, "0 < v_min < v_max"),
        (1.0, 10.0, {"base": 1.0}, "base > 1"),
        (1.0, 10.0, {"minor_subs": (15.0,)}, "strictly inside"),
    ],
)
def test_log_ticks_rejects_invalid_input(v_min: float, v_max: float, kwargs: dict, match: str) -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match=match):
        log_ticks(v_min, v_max, **kwargs)
