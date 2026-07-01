# Assumptions

The following assumptions are made for the development and operation of DriveVitals:

- Vehicles support the standard OBD-II protocol.
- An ELM327 adapter (Bluetooth or Wi-Fi) is available for ECU communication.
- Supported PIDs vary across different vehicle manufacturers and models.
- The vehicle’s ignition system must be active for telemetry data acquisition.
- ECU responses follow standard OBD-II encoding formats for supported parameters.
- Network connectivity is available for dashboard updates (if deployed remotely).
- Collected telemetry data is sufficiently accurate for rule-based analysis.