"""Direct, example-based tests for every pure function in features.py —
the How-to-Design-Functions "examples" made executable. These test the
feature-engineering layer in isolation from the engine's signal/evidence
reasoning (covered separately in test_engine.py)."""

import math

from mirage_ai.features import (
    band_score,
    click_features,
    cv,
    density_features,
    focus_features,
    hidden_ratio,
    idle_features,
    latency_samples,
    mouse_features,
    rise_score,
    scroll_features,
    typing_features,
)


# -- cv --------------------------------------------------------------------


def test_cv_of_constant_values_is_zero():
    assert cv([2.0, 2.0, 2.0, 2.0]) == 0.0


def test_cv_of_varied_values_is_positive():
    assert cv([1.0, 5.0, 2.0, 8.0]) > 0.0


def test_cv_is_none_for_fewer_than_two_values():
    assert cv([]) is None
    assert cv([5.0]) is None


def test_cv_is_none_for_near_zero_mean():
    assert cv([0.0, 0.0, 0.0]) is None


# -- band_score / rise_score -------------------------------------------------


def test_band_score_outside_range_is_zero():
    assert band_score(-1, 0, 1, 2, 3) == 0.0
    assert band_score(4, 0, 1, 2, 3) == 0.0


def test_band_score_plateau_is_one():
    assert band_score(1.5, 0, 1, 2, 3) == 1.0


def test_band_score_rises_and_falls_linearly():
    assert band_score(0.5, 0, 1, 2, 3) == 0.5
    assert band_score(2.5, 0, 1, 2, 3) == 0.5


def test_rise_score_endpoints_and_midpoint():
    assert rise_score(0, 0, 10) == 0.0
    assert rise_score(10, 0, 10) == 1.0
    assert rise_score(5, 0, 10) == 0.5
    assert rise_score(-5, 0, 10) == 0.0
    assert rise_score(50, 0, 10) == 1.0


# -- mouse_features ----------------------------------------------------------


def test_mouse_features_none_below_minimum_moves():
    assert mouse_features([(0.0, 0.0, 0.0)] * 7) is None


def _natural_moves(n=40):
    moves = []
    x = y = 0.0
    t = 0.0
    for i in range(n):
        t += 100.0 + (i % 5) * 20.0
        x += 10.0 + (i % 3) * 15.0
        y += (i % 4) * 8.0 - 12.0
        moves.append((t, x, y))
    return moves


def test_mouse_features_reports_sample_count_and_positive_entropy():
    feats = mouse_features(_natural_moves())
    assert feats is not None
    assert feats["n"] >= 6
    assert feats["entropy"] > 0.0


def test_mouse_features_straight_line_has_zero_entropy_and_curvature():
    # a straight line: constant direction, constant step, constant dt.
    moves = [(float(i) * 100.0, float(i) * 10.0, 0.0) for i in range(20)]
    feats = mouse_features(moves)
    assert feats is not None
    assert feats["entropy"] == 0.0
    assert feats["curvature"] == 0.0
    assert feats["reversal_rate"] == 0.0


def test_mouse_features_jiggler_has_high_reversal_rate():
    # oscillate back and forth along the x axis every step.
    moves = []
    x = 0.0
    for i in range(20):
        x += 14.0 if i % 2 == 0 else -14.0
        moves.append((float(i) * 100.0, x, 0.0))
    feats = mouse_features(moves)
    assert feats is not None
    assert feats["reversal_rate"] > 0.9


def test_mouse_features_ignores_gaps_larger_than_max_move_gap():
    # a single huge gap should be dropped, not treated as one giant segment.
    moves = _natural_moves(10) + [(1_000_000.0, 999.0, 999.0)]
    feats = mouse_features(moves)
    assert feats is not None
    assert feats["n"] == 9  # 10 natural moves -> 9 segments; the gapped one is dropped


# -- typing_features ----------------------------------------------------------


def test_typing_features_none_below_minimum_keys():
    assert typing_features([float(i) for i in range(5)]) is None


def test_typing_features_separates_active_typing_from_pauses():
    # 6 keys typed close together, then a long thinking pause, then 6 more.
    burst_a = [i * 150.0 for i in range(6)]
    pause_start = burst_a[-1] + 5_000.0
    burst_b = [pause_start + i * 150.0 for i in range(6)]
    feats = typing_features(burst_a + burst_b)
    assert feats is not None
    assert feats["pause_count"] == 1
    assert feats["n"] == 10  # 11 deltas total, 1 is a pause


def test_typing_features_none_when_all_deltas_are_pauses():
    keys = [0.0, 5_000.0, 10_000.0, 15_000.0, 20_000.0, 25_000.0]
    assert typing_features(keys) is None


# -- click_features / scroll_features -----------------------------------------


def test_click_features_none_below_minimum_clicks():
    assert click_features([0.0, 1000.0, 2000.0]) is None


def test_click_features_reports_interval_variability():
    feats = click_features([0.0, 1000.0, 2000.0, 3000.0, 4000.0])
    assert feats is not None
    assert feats["interval_cv"] == 0.0  # perfectly even intervals


def test_scroll_features_direction_change_rate():
    # alternating up/down scrolls -> every transition is a direction change.
    scrolls = [(float(i) * 500.0, 100.0 if i % 2 == 0 else -100.0) for i in range(6)]
    feats = scroll_features(scrolls)
    assert feats is not None
    assert feats["direction_change_rate"] == 1.0


# -- idle_features -------------------------------------------------------------


def test_idle_features_none_below_minimum_timestamps():
    assert idle_features([float(i) for i in range(5)], idle_gap_ms=5_000.0) is None


def test_idle_features_counts_gaps_above_threshold():
    times = [float(i) * 500.0 for i in range(10)]  # dense, no idle
    times.append(times[-1] + 10_000.0)  # one big gap
    times.append(times[-1] + 500.0)
    feats = idle_features(times, idle_gap_ms=5_000.0)
    assert feats is not None
    assert feats["idle_count"] == 1


# -- focus_features / hidden_ratio ---------------------------------------------


def test_focus_features_counts_losses_in_window():
    result = focus_features([1_000.0, 2_000.0, 90_000.0], window_start=0.0, now=60_000.0)
    assert result["losses"] == 2


def test_hidden_ratio_zero_with_no_transitions():
    assert hidden_ratio([], window_start=0.0, now=10_000.0) == 0.0


def test_hidden_ratio_half_when_hidden_for_half_the_window():
    events = [(0.0, "hidden"), (5_000.0, "visible")]
    assert hidden_ratio(events, window_start=0.0, now=10_000.0) == 0.5


def test_hidden_ratio_full_when_still_hidden_at_window_end():
    events = [(0.0, "hidden")]
    assert hidden_ratio(events, window_start=0.0, now=10_000.0) == 1.0


# -- latency_samples / density_features -----------------------------------------


def test_latency_samples_pairs_focus_gain_with_next_interaction():
    samples = latency_samples(focus_gained_times=[1_000.0], interaction_times=[500.0, 1_300.0, 2_000.0])
    assert samples == [300.0]


def test_latency_samples_drops_values_over_cap():
    samples = latency_samples(focus_gained_times=[0.0], interaction_times=[20_000.0])
    assert samples == []


def test_density_features_none_below_minimum_events():
    assert density_features([float(i) for i in range(5)], window_start=0.0, now=10_000.0) is None


def test_density_features_reports_events_per_min():
    times = [float(i) * 1_000.0 for i in range(12)]
    feats = density_features(times, window_start=0.0, now=12_000.0)
    assert feats is not None
    assert feats["n"] == 12
    assert feats["events_per_min"] == math.floor(12 / (12_000.0 / 60_000.0))
