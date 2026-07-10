EVENT_METADATA = {
    "overspeed": {
        "title": "Overspeed Detected",
    },

    "high_engine_load": {
        "title": "High Engine Load",
    },

    "high_rpm": {
        "title": "High Engine RPM",
    },

    "high_coolant_temperature": {
        "title": "Coolant Temperature High",
    },

    "high_fuel_consumption": {
        "title": "High Fuel Consumption",
    },

    "excessive_idle": {
        "title": "Excessive Idle",
    },
}

def enrich_event(event):

    metadata = EVENT_METADATA.get(
        event["event"],
        {}
    )


    event["title"] = metadata.get(
        "title",
        event["event"]
    )


    event["icon"] = metadata.get(
        "icon",
        "⚠️"
    )


    event["category"] = metadata.get(
        "category",
        "Unknown"
    )


    return event