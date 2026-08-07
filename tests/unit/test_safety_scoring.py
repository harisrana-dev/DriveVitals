"""Unit tests for the canonical driver safety score and trip grade."""

from backend.analytics.driver_statistics.safety import (
    compute_grade,
    compute_safety_score,
)


def test_clean_trip_scores_perfect():
    score = compute_safety_score(
        harsh_braking_count=0,
        harsh_acceleration_count=0,
        overspeed_count=0,
        distance_km=5.0,
    )
    assert score == 100.0
    assert compute_grade(score) == "A"


def test_normal_short_trip_is_not_critical():
    # A single overspeed episode over a 4 km trip must not crater the
    # score to 0%/F. It should land in Average/Good territory.
    score = compute_safety_score(
        harsh_braking_count=0,
        harsh_acceleration_count=0,
        overspeed_count=1,
        distance_km=4.0,
    )
    assert 60.0 <= score <= 90.0
    assert compute_grade(score) in {"B", "C", "D"}


def test_few_events_on_short_trip_stay_outside_critical():
    # Two genuine events (1 harsh brake + 1 overspeed) over a short
    # trip must remain Average, never Critical/F.
    score = compute_safety_score(
        harsh_braking_count=1,
        harsh_acceleration_count=0,
        overspeed_count=1,
        distance_km=4.0,
    )
    assert 55.0 <= score <= 90.0
    assert compute_grade(score) in {"B", "C", "D"}


def test_genuinely_bad_trip_reaches_critical():
    score = compute_safety_score(
        harsh_braking_count=6,
        harsh_acceleration_count=3,
        overspeed_count=4,
        distance_km=3.0,
    )
    assert score < 40.0
    assert compute_grade(score) == "F"


def test_zero_distance_with_events_is_zero():
    score = compute_safety_score(
        harsh_braking_count=2,
        harsh_acceleration_count=0,
        overspeed_count=0,
        distance_km=0.0,
    )
    assert score == 0.0
    assert compute_grade(score) == "F"


def test_score_never_leaves_unit_range():
    score = compute_safety_score(
        harsh_braking_count=50,
        harsh_acceleration_count=50,
        overspeed_count=50,
        high_rpm_count=50,
        distance_km=0.5,
    )
    assert 0.0 <= score <= 100.0


def test_grade_boundaries():
    assert compute_grade(95) == "A"
    assert compute_grade(90) == "A"
    assert compute_grade(89.99) == "B"
    assert compute_grade(80) == "B"
    assert compute_grade(79.99) == "C"
    assert compute_grade(70) == "C"
    assert compute_grade(69.99) == "D"
    assert compute_grade(60) == "D"
    assert compute_grade(59.99) == "F"
