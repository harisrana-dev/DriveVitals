"""Units and PID codes for the Virtual Sensor Framework.

Scope note: constants here are defined only for the 10 sensors that
have a real, direct `VehicleState` source (see `virtual_sensor_provider.py`
for the full accounting of what was and wasn't implemented, and why).
No unit or PID is defined for a sensor that was reported as an
integration gap -- there is nothing to name a unit or PID for.
"""

from __future__ import annotations

# --- Units -------------------------------------------------------------

UNIT_KMH: str = "km/h"
UNIT_RPM: str = "rpm"
UNIT_PERCENT: str = "%"
UNIT_CELSIUS: str = "degC"
UNIT_VOLTS: str = "V"
UNIT_KM: str = "km"
UNIT_GEAR: str = "gear"

# --- OBD-II Mode 1 (show current data) --------------------------------------

OBD_MODE_CURRENT_DATA: str = "01"

# --- Standard OBD-II PIDs ----------------------------------------------
#
# These are real, standardized Mode 01 PIDs (SAE J1979). Sensors that
# have a genuine VehicleState source map to these where a standard PID
# exists.

PID_ENGINE_LOAD: str = "0x04"
PID_COOLANT_TEMP: str = "0x05"  # Not used: no distinct coolant field exists (see gap report).
PID_ENGINE_RPM: str = "0x0C"
PID_VEHICLE_SPEED: str = "0x0D"
PID_INTAKE_AIR_TEMP: str = "0x0F"  # Not used: not requested/not modeled.
PID_MAF: str = "0x10"  # Not used: not requested/not modeled.
PID_THROTTLE_POSITION: str = "0x11"  # Not used: no VehicleState source (see gap report).
PID_FUEL_LEVEL: str = "0x2F"
PID_CONTROL_MODULE_VOLTAGE: str = "0x42"
PID_FUEL_RATE: str = "0x5E"  # Not used: no VehicleState source (see gap report).

# --- DriveVitals custom PIDs -------------------------------------------
#
# No standard OBD-II PID exists for these signals; assigned in the
# manufacturer-specific PID range per SAE J1979 convention, prefixed
# distinctly so they're never confused with a standard PID.

PID_DV_GEAR_POSITION: str = "DV-2101"
PID_DV_ENGINE_TEMPERATURE: str = "DV-2102"
PID_DV_ODOMETER: str = "DV-2103"
PID_DV_BRAKE_PAD_HEALTH: str = "DV-2104"
PID_DV_TYRE_HEALTH: str = "DV-2105"