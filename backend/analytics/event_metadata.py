EVENT_METADATA = {

    "overspeed": {
        "title": "Overspeeding",
        "icon": "🚨",
        "category": "Driver Behaviour",
        "severity": "WARNING",
    },


    "high_rpm": {
        "title": "High Engine RPM",
        "icon": "⚙️",
        "category": "Vehicle Health",
        "severity": "WARNING",
    },


    "high_engine_load": {
        "title": "High Engine Load",
        "icon": "🔥",
        "category": "Vehicle Health",
        "severity": "WARNING",
    },


    "high_coolant_temperature": {
        "title": "High Coolant Temperature",
        "icon": "🌡️",
        "category": "Critical",
        "severity": "CRITICAL",
    },


    "high_fuel_consumption": {
        "title": "High Fuel Consumption",
        "icon": "⛽",
        "category": "Fuel Efficiency",
        "severity": "WARNING",
    },


    "excessive_idle": {
        "title": "Excessive Idle",
        "icon": "🅿️",
        "category": "Driver Behaviour",
        "severity": "INFO",
    }

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