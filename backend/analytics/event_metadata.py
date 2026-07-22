"""Event metadata: static lookup for rule event display properties.

Maps rule event keys to human-readable titles and categories
for dashboard rendering. Updated for Digital Twin sensor catalog.
"""

from __future__ import annotations

EVENT_METADATA: dict[str, dict[str, str]] = {
    "overspeed": {
        "title": "Overspeed Detected",
        "category": "driver_behaviour",
    },
    "high_rpm": {
        "title": "High Engine RPM",
        "category": "vehicle_health",
    },
    "high_engine_load": {
        "title": "High Engine Load",
        "category": "vehicle_health",
    },
    "high_engine_temperature": {
        "title": "Engine Temperature High",
        "category": "vehicle_health",
    },
    "low_fuel": {
        "title": "Low Fuel Level",
        "category": "fuel_efficiency",
    },
    "low_battery": {
        "title": "Low Battery Voltage",
        "category": "vehicle_health",
    },
    "excessive_idle": {
        "title": "Excessive Idle",
        "category": "driver_behaviour",
    },
}


def enrich_event(event: dict) -> dict:
    """Decorate an event dict with display metadata.

    Args:
        event: Dict with at least an "event" key.

    Returns:
        The same dict, augmented with title, icon, and category.
    """
    metadata = EVENT_METADATA.get(event.get("event", ""), {})
    event["title"] = metadata.get("title", event.get("event", ""))
    event["icon"] = metadata.get("icon", "\u26a0\ufe0f")
    event["category"] = metadata.get("category", "Unknown")
    return event
