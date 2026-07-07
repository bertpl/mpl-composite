import pytest

from mpl_composite.axis import ScaleLinear, ScaleLinLog, ScaleLog, linear_ticks, log_ticks
from mpl_composite.geometry import Range
from mpl_composite.transforms import TransformLinear, TransformLinLog, TransformLog


# ==================================================================================================
#  transform() dispatch
# ==================================================================================================
def test_scales_build_their_transform_kind() -> None:
    # --- arrange ----------------------
    value_range, ax_range = Range(1.0, 100.0), Range(0.0, 1.0)

    # --- act --------------------------
    t_lin = ScaleLinear().transform(value_range, ax_range)
    t_log = ScaleLog().transform(value_range, ax_range)
    t_linlog = ScaleLinLog(lin_max=10.0, lin_fraction=0.3).transform(value_range, ax_range)

    # --- assert -----------------------
    assert isinstance(t_lin, TransformLinear)
    assert isinstance(t_log, TransformLog)
    assert isinstance(t_linlog, TransformLinLog)


def test_transform_reverse_pass_through() -> None:
    # --- act --------------------------
    t = ScaleLinear().transform(Range(0.0, 1.0), Range(0.0, 1.0), reverse=True)

    # --- assert -----------------------
    assert t.is_reverse


# ==================================================================================================
#  ticks() dispatch
# ==================================================================================================
def test_scale_linear_ticks_match_raw_algorithm() -> None:
    # --- act / assert -----------------
    assert ScaleLinear().ticks(Range(0.0, 10.0)) == linear_ticks(0.0, 10.0)


def test_scale_linear_ticks_carry_scale_parameters() -> None:
    # --- act --------------------------
    ticks = ScaleLinear(n_minor_per_major=1).ticks(Range(0.0, 10.0), n_major_target=3)

    # --- assert -----------------------
    assert ticks == linear_ticks(0.0, 10.0, n_major_target=3, n_minor_per_major=1)


def test_scale_log_ticks_match_raw_algorithm() -> None:
    # --- act / assert -----------------
    assert ScaleLog().ticks(Range(1.0, 1000.0)) == log_ticks(1.0, 1000.0)
    assert ScaleLog(base=2.0, minor_subs=(1.5,)).ticks(Range(1.0, 16.0)) == log_ticks(
        1.0, 16.0, base=2.0, minor_subs=(1.5,)
    )


def test_scale_linlog_ticks_share_the_seam_and_one_fmt() -> None:
    # --- arrange ----------------------
    scale = ScaleLinLog(lin_max=1.0, lin_fraction=0.4)

    # --- act --------------------------
    ticks = scale.ticks(Range(0.0, 1000.0), n_major_target=5)

    # --- assert -----------------------
    assert 1.0 in ticks.major  # the seam tick, exactly once (majors are a set-merge)
    assert {10.0, 100.0, 1000.0} <= set(ticks.major)  # decades above the seam
    assert min(ticks.major) >= 0.0
    assert ticks.major_labels == tuple(f"{v:g}" for v in ticks.major)  # one fmt pass


@pytest.mark.parametrize(
    "value_range, equivalent",
    [
        (Range(0.0, 0.8), linear_ticks(0.0, 0.8)),  # fully below the seam
        (Range(10.0, 1000.0), log_ticks(10.0, 1000.0)),  # fully above the seam
    ],
)
def test_scale_linlog_ticks_degrade_to_single_segment(value_range: Range, equivalent) -> None:
    # --- act / assert -----------------
    assert ScaleLinLog(lin_max=1.0, lin_fraction=0.25).ticks(value_range) == equivalent


def test_scale_linlog_ticks_budget_follows_lin_fraction() -> None:
    # --- arrange ----------------------
    value_range = Range(0.0, 1000.0)

    # --- act --------------------------
    narrow = ScaleLinLog(lin_max=10.0, lin_fraction=0.2).ticks(value_range, n_major_target=10)
    wide = ScaleLinLog(lin_max=10.0, lin_fraction=0.8).ticks(value_range, n_major_target=10)

    # --- assert -----------------------
    below_seam = [v for v in wide.major if v < 10.0]
    assert len(below_seam) > len([v for v in narrow.major if v < 10.0])


def test_scale_linlog_ticks_tolerate_an_ugly_seam() -> None:
    # --- act --------------------------
    ticks = ScaleLinLog(lin_max=7.3, lin_fraction=0.5).ticks(Range(0.0, 730.0))

    # --- assert -----------------------
    assert 7.3 in ticks.major  # the ugly seam value is still the shared tick
    assert ticks.major == tuple(sorted(set(ticks.major)))  # sorted, no duplicates


def test_scale_linlog_ticks_sub_decade_log_segment_falls_back() -> None:
    # --- act --------------------------
    ticks = ScaleLinLog(lin_max=1.0, lin_fraction=0.5).ticks(Range(0.0, 3.0))

    # --- assert -----------------------
    assert 1.0 in ticks.major
    assert max(ticks.major) <= 3.0
    assert len(ticks.major) >= 3  # the sub-decade segment still contributes ticks


# ==================================================================================================
#  expand()
# ==================================================================================================
@pytest.mark.parametrize(
    "values, expected",
    [
        ([0.0, 10.0], Range(-0.5, 10.5)),
        ([10.0, 0.0, 5.0], Range(-0.5, 10.5)),  # order-insensitive
        ([5.0], Range(4.75, 5.25)),  # degenerate: pad by margin * |value|
        ([0.0], Range(-0.05, 0.05)),  # degenerate at zero: pad by margin * 1
    ],
)
def test_scale_linear_expand(values: list, expected: Range) -> None:
    # --- act --------------------------
    expanded = ScaleLinear().expand(values)

    # --- assert -----------------------
    assert expanded.min == pytest.approx(expected.min)
    assert expanded.max == pytest.approx(expected.max)


def test_scale_log_expand_pads_in_log_space() -> None:
    # --- act --------------------------
    expanded = ScaleLog().expand([1.0, 100.0])  # 2 decades, 5% pad = 0.1 decade per side

    # --- assert -----------------------
    assert expanded.min == pytest.approx(10.0**-0.1)
    assert expanded.max == pytest.approx(10.0**2.1)


def test_scale_log_expand_degenerate_pads_by_base_factor() -> None:
    # --- act --------------------------
    expanded = ScaleLog().expand([5.0])

    # --- assert -----------------------
    assert expanded.min == pytest.approx(5.0 * 10.0**-0.05)
    assert expanded.max == pytest.approx(5.0 * 10.0**0.05)


def test_scale_log_expand_rejects_non_positive_values() -> None:
    # --- act / assert -----------------
    with pytest.raises(ValueError, match="strictly positive"):
        ScaleLog().expand([-1.0, 5.0])


def test_scale_linlog_expand_pads_each_edge_in_its_segment_space() -> None:
    # --- arrange ----------------------
    scale = ScaleLinLog(lin_max=1.0, lin_fraction=0.25)

    # --- act --------------------------
    expanded = scale.expand([0.0, 100.0])

    # --- assert -----------------------
    assert expanded.min == pytest.approx(0.0 - 0.05 * 1.0)  # linear pad below the seam
    assert expanded.max == pytest.approx(100.0 * 100.0**0.05)  # log pad above the seam


def test_scale_linlog_expand_all_values_below_seam() -> None:
    # --- act --------------------------
    expanded = ScaleLinLog(lin_max=10.0, lin_fraction=0.5).expand([1.0, 5.0])

    # --- assert -----------------------
    assert expanded.min == pytest.approx(1.0 - 0.05 * 4.0)  # linear pad toward min(hi, seam)
    assert expanded.max == pytest.approx(5.0 + 0.05 * 4.0)  # linear pad (still below the seam)


def test_scale_linlog_expand_degenerate() -> None:
    # --- act --------------------------
    expanded = ScaleLinLog(lin_max=1.0, lin_fraction=0.25).expand([3.0])

    # --- assert -----------------------
    assert expanded.min == pytest.approx(2.85)
    assert expanded.max == pytest.approx(3.15)


# ==================================================================================================
#  mid_point()
# ==================================================================================================
def test_mid_point_per_scale() -> None:
    # --- act / assert -----------------
    assert ScaleLinear().mid_point(Range(0.0, 10.0)) == pytest.approx(5.0)
    assert ScaleLog().mid_point(Range(1.0, 100.0)) == pytest.approx(10.0)  # geometric mean
    # lin-log with 25% linear share: the visual center sits in the log part
    assert ScaleLinLog(lin_max=1.0, lin_fraction=0.25).mid_point(Range(0.0, 1000.0)) == pytest.approx(10.0)
