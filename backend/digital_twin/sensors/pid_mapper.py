"""PID mapper: maps sensor name to PID metadata.

This is metadata only -- it does not read `VehicleState`, format
telemetry payloads, or communicate with anything. It answers exactly
one question: "what PID identifies this signal, and is it a standard
OBD-II PID or a DriveVitals custom one?"
"""

from __future__ import annotations

from dataclasses import dataclass

from digital_twin.sensors import sensor_constants as const


@dataclass(frozen=True)
class PidMetadata:
    """Metadata identifying a signal by its OBD-II (or custom) PID.

    Attributes:
        pid_code: The PID code, e.g. "0x0C" for a standard PID or
            "DV-2101" for a DriveVitals custom one.
        mode: The OBD-II mode this PID is read under (e.g. "01" for
            Mode 1 / show current data).
        pid_name: Human-readable name of the signal.
        is_standard: Whether this is a real, standardized OBD-II PID
            (SAE J1979) as opposed to a DriveVitals custom PID.
    """

    pid_code: str
    mode: str
    pid_name: str
    is_standard: bool


#: Sensor name -> PID metadata, for every sensor that has a real
#: VehicleState source (see `virtual_sensor_provider.py` for the full
#: gap report on requested sensors that are not in this map because
#: they were not implemented).
PID_MAP: dict[str, PidMetadata] = {
    "vehicle_speed": PidMetadata(
        pid_code=const.PID_VEHICLE_SPEED,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Vehicle Speed",
        is_standard=True,
    ),
    "engine_rpm": PidMetadata(
        pid_code=const.PID_ENGINE_RPM,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Engine RPM",
        is_standard=True,
    ),
    "gear_position": PidMetadata(
        pid_code=const.PID_DV_GEAR_POSITION,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Gear Position",
        is_standard=False,
    ),
    "fuel_level": PidMetadata(
        pid_code=const.PID_FUEL_LEVEL,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Fuel Level",
        is_standard=True,
    ),
    "engine_load": PidMetadata(
        pid_code=const.PID_ENGINE_LOAD,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Calculated Engine Load",
        is_standard=True,
    ),
    "engine_temperature": PidMetadata(
        pid_code=const.PID_DV_ENGINE_TEMPERATURE,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Engine Temperature",
        is_standard=False,
    ),
    "battery_voltage": PidMetadata(
        pid_code=const.PID_CONTROL_MODULE_VOLTAGE,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Control Module Voltage",
        is_standard=True,
    ),
    "odometer": PidMetadata(
        pid_code=const.PID_DV_ODOMETER,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Odometer",
        is_standard=False,
    ),
    "brake_pad_health": PidMetadata(
        pid_code=const.PID_DV_BRAKE_PAD_HEALTH,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Brake Pad Health",
        is_standard=False,
    ),
    "tyre_health": PidMetadata(
        pid_code=const.PID_DV_TYRE_HEALTH,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Tyre Health",
        is_standard=False,
    ),
    "fuel_rate": PidMetadata(
        pid_code=const.PID_FUEL_RATE,
        mode=const.OBD_MODE_CURRENT_DATA,
        pid_name="Fuel Rate",
        is_standard=True,
    ),
}


def get_pid_metadata(sensor_name: str) -> PidMetadata | None:
    """Look up PID metadata for a sensor by name.

    Args:
        sensor_name: The sensor's name (matches `Sensor.sensor_name`).

    Returns:
        The matching PidMetadata, or `None` if no PID mapping exists
        for that sensor name.
    """
    return PID_MAP.get(sensor_name)