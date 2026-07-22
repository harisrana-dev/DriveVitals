"""Tests for EventManager lifecycle tracking."""

from datetime import datetime

from analytics.event_manager import EventManager


def _ts(hour: int = 12, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2026, 7, 21, hour, minute, second)


def test_first_violation_creates_active_event():
    em = EventManager()
    em.update(
        active_event_types={("v1", "overspeed")},
        event_snapshots={
            ("v1", "overspeed"): {
                "rule_id": "DV-R001",
                "category": "driver_behaviour",
                "severity": "WARNING",
                "value": 130.0,
                "threshold": 120.0,
                "timestamp": _ts(),
            }
        },
        current_tick=1,
    )
    active = em.get_active_events()
    assert len(active) == 1
    assert active[0].event_type == "overspeed"
    assert active[0].status == "ACTIVE"
    assert active[0].occurrences == 1
    assert active[0].first_seen_tick == 1
    assert active[0].last_seen_tick == 1
    print("PASS: first_violation_creates_active_event")


def test_repeated_violation_increments():
    em = EventManager()
    for tick in range(1, 4):
        em.update(
            active_event_types={("v1", "overspeed")},
            event_snapshots={
                ("v1", "overspeed"): {
                    "rule_id": "DV-R001",
                    "category": "driver_behaviour",
                    "severity": "WARNING",
                    "value": 130.0 + tick,
                    "threshold": 120.0,
                    "timestamp": _ts(second=tick),
                }
            },
            current_tick=tick,
        )
    active = em.get_active_events()
    assert len(active) == 1
    assert active[0].occurrences == 3
    assert active[0].last_seen_tick == 3
    assert active[0].latest_value == 133.0
    print("PASS: repeated_violation_increments")


def test_event_resolves_when_condition_disappears():
    em = EventManager()
    # Active
    em.update(
        active_event_types={("v1", "overspeed")},
        event_snapshots={
            ("v1", "overspeed"): {
                "rule_id": "DV-R001", "category": "driver_behaviour",
                "severity": "WARNING", "value": 130.0, "threshold": 120.0,
                "timestamp": _ts(),
            }
        },
        current_tick=1,
    )
    # Resolved
    em.update(
        active_event_types=set(),
        event_snapshots={},
        current_tick=2,
    )
    assert len(em.get_active_events()) == 0
    resolved = em.get_resolved_events()
    assert len(resolved) == 1
    assert resolved[0].status == "RESOLVED"
    assert resolved[0].occurrences == 1
    print("PASS: event_resolves_when_condition_disappears")


def test_different_vehicles_independent():
    em = EventManager()
    em.update(
        active_event_types={("v1", "overspeed"), ("v2", "high_rpm")},
        event_snapshots={
            ("v1", "overspeed"): {
                "rule_id": "DV-R001", "category": "driver_behaviour",
                "severity": "WARNING", "value": 130.0, "threshold": 120.0,
                "timestamp": _ts(),
            },
            ("v2", "high_rpm"): {
                "rule_id": "DV-R002", "category": "vehicle_health",
                "severity": "WARNING", "value": 5500.0, "threshold": 5000.0,
                "timestamp": _ts(),
            },
        },
        current_tick=1,
    )
    assert len(em.get_active_events()) == 2

    # v1 resolves, v2 stays
    em.update(
        active_event_types={("v2", "high_rpm")},
        event_snapshots={
            ("v2", "high_rpm"): {
                "rule_id": "DV-R002", "category": "vehicle_health",
                "severity": "WARNING", "value": 5500.0, "threshold": 5000.0,
                "timestamp": _ts(second=1),
            }
        },
        current_tick=2,
    )
    active = em.get_active_events()
    assert len(active) == 1
    assert active[0].vehicle_id == "v2"
    resolved = em.get_resolved_events()
    assert len(resolved) == 1
    assert resolved[0].vehicle_id == "v1"
    print("PASS: different_vehicles_independent")


def test_different_event_types_independent():
    em = EventManager()
    em.update(
        active_event_types={("v1", "overspeed"), ("v1", "high_rpm")},
        event_snapshots={
            ("v1", "overspeed"): {
                "rule_id": "DV-R001", "category": "driver_behaviour",
                "severity": "WARNING", "value": 130.0, "threshold": 120.0,
                "timestamp": _ts(),
            },
            ("v1", "high_rpm"): {
                "rule_id": "DV-R002", "category": "vehicle_health",
                "severity": "WARNING", "value": 5500.0, "threshold": 5000.0,
                "timestamp": _ts(),
            },
        },
        current_tick=1,
    )

    # overspeed resolves, high_rpm stays
    em.update(
        active_event_types={("v1", "high_rpm")},
        event_snapshots={
            ("v1", "high_rpm"): {
                "rule_id": "DV-R002", "category": "vehicle_health",
                "severity": "WARNING", "value": 5600.0, "threshold": 5000.0,
                "timestamp": _ts(second=1),
            }
        },
        current_tick=2,
    )
    active = em.get_active_events()
    assert len(active) == 1
    assert active[0].event_type == "high_rpm"
    resolved = em.get_resolved_events()
    assert len(resolved) == 1
    assert resolved[0].event_type == "overspeed"
    print("PASS: different_event_types_independent")


def test_high_engine_load_included():
    em = EventManager()
    em.update(
        active_event_types={("v1", "high_engine_load")},
        event_snapshots={
            ("v1", "high_engine_load"): {
                "rule_id": "DV-R003", "category": "vehicle_health",
                "severity": "WARNING", "value": 91.0, "threshold": 85.0,
                "timestamp": _ts(),
            }
        },
        current_tick=1,
    )
    active = em.get_active_events()
    assert len(active) == 1
    assert active[0].event_type == "high_engine_load"
    assert active[0].rule_id == "DV-R003"
    print("PASS: high_engine_load_included")


def test_to_dict():
    em = EventManager()
    em.update(
        active_event_types={("v1", "overspeed")},
        event_snapshots={
            ("v1", "overspeed"): {
                "rule_id": "DV-R001", "category": "driver_behaviour",
                "severity": "WARNING", "value": 130.0, "threshold": 120.0,
                "timestamp": _ts(),
            }
        },
        current_tick=1,
    )
    d = em.get_active_events()[0].to_dict()
    assert isinstance(d, dict)
    assert d["event_type"] == "overspeed"
    assert d["status"] == "ACTIVE"
    assert d["occurrences"] == 1
    print("PASS: to_dict")


if __name__ == "__main__":
    test_first_violation_creates_active_event()
    test_repeated_violation_increments()
    test_event_resolves_when_condition_disappears()
    test_different_vehicles_independent()
    test_different_event_types_independent()
    test_high_engine_load_included()
    test_to_dict()
    print("\nALL EventManager TESTS PASSED")
