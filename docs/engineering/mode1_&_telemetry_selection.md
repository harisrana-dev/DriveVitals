# Mode 01 & Telemetry Selection

## Purpose

Mode 01 is the most important OBD-II operating mode for DriveVitals. It allows the system to request **live telemetry data** from the vehicle's Engine Control Unit (ECU) while the vehicle is running.

Unlike other OBD-II modes that focus on diagnostics or vehicle information, Mode 01 continuously provides real-time sensor values that DriveVitals uses for driver behavior analysis, vehicle health monitoring, fuel efficiency estimation, and future machine learning models.

---

# OBD-II Modes Overview

| Mode | Purpose | DriveVitals Usage |
|------|---------|-------------------|
| 01 | Current Live Data | ✅ Primary Mode |
| 02 | Freeze Frame Data | Future |
| 03 | Read Diagnostic Trouble Codes (DTCs) | Future |
| 04 | Clear DTCs | Not Required |
| 09 | Vehicle Information (VIN, Calibration, etc.) | Future |

For Version 1 of DriveVitals, almost every request sent to the ECU will use **Mode 01**.

---

# How Mode 01 Communication Works

The backend continuously sends requests to the ECU using the following format:

```
Mode + PID
```

Example:

```
01 0D
```

Meaning:

- **01** → Current Live Data
- **0D** → Vehicle Speed

The ECU responds with hexadecimal data.

Example:

```
41 0D 3C
```

Where:

| Byte | Meaning |
|------|---------|
| 41 | Response to Mode 01 |
| 0D | Vehicle Speed PID |
| 3C | Speed Value (Hexadecimal) |

Hexadecimal value:

```
3C (Hex)
```

↓

```
60 (Decimal)
```

Vehicle Speed = **60 km/h**

---

# Example: Engine RPM

Request:

```
01 0C
```

Response:

```
41 0C 1A F8
```

Formula defined by the OBD-II standard:

```
RPM = ((A × 256) + B) / 4
```

Where:

```
A = 1A = 26
B = F8 = 248
```

Calculation:

```
((26 × 256) + 248) / 4
= 1726 RPM
```

DriveVitals performs this decoding automatically before storing or displaying the value.

---

# Core Telemetry Parameters (Version 1)

These parameters are essential for the first version of DriveVitals.

| PID | Parameter | Importance | Used For |
|------|-----------|------------|----------|
| 0C | Engine RPM | ⭐⭐⭐⭐⭐ | Driver Behavior, Fuel Efficiency, Engine Health |
| 0D | Vehicle Speed | ⭐⭐⭐⭐⭐ | Driver Behavior |
| 05 | Coolant Temperature | ⭐⭐⭐⭐ | Vehicle Health |
| 04 | Engine Load | ⭐⭐⭐⭐ | Engine Stress Analysis |
| 11 | Throttle Position | ⭐⭐⭐⭐⭐ | Aggressive Acceleration Detection |
| 10 | Mass Air Flow (MAF) | ⭐⭐⭐⭐⭐ | Fuel Efficiency Estimation |

These six parameters provide enough information to build a functional MVP of DriveVitals.

---

# Additional Useful Parameters

The following parameters improve analytics but are not mandatory for the first release.

| PID | Parameter | Purpose |
|------|-----------|---------|
| 0F | Intake Air Temperature | Engine Performance |
| 2F | Fuel Level | Trip Statistics |
| 06 | Short-Term Fuel Trim | Fuel System Analysis |
| 07 | Long-Term Fuel Trim | Fuel Efficiency |
| 0E | Ignition Timing | Engine Performance |
| 42 | Battery Voltage* | Electrical System Monitoring |

> **Note:** Battery Voltage support varies by manufacturer and may not be available through a standardized PID on all vehicles.

---

# Future Telemetry Parameters

These parameters are planned for future versions of DriveVitals.

- Oxygen Sensor Data
- Air-Fuel Ratio
- Catalyst Temperature
- Evaporative Emission System Data
- Freeze Frame Data
- Diagnostic Trouble Codes (DTCs)
- Vehicle Identification Number (VIN)

These features will enhance predictive maintenance and advanced diagnostics.

---

# Telemetry-to-Feature Mapping

## Driver Behavior Analysis

Required Parameters:

- Engine RPM
- Vehicle Speed
- Throttle Position
- Engine Load

Example:

```
High RPM
+
High Throttle Position
=
Aggressive Acceleration
```

---

## Fuel Efficiency Estimation

Required Parameters:

- Mass Air Flow (MAF)
- Engine RPM
- Vehicle Speed
- Fuel Trim

---

## Vehicle Health Monitoring

Required Parameters:

- Coolant Temperature
- Engine Load
- Battery Voltage
- Diagnostic Trouble Codes (Future)

---

## Predictive Maintenance

Required Parameters:

- Historical RPM
- Engine Load
- Coolant Temperature
- Fuel Trim
- Historical Telemetry Database

---

# Recommended Polling Frequency

Not every parameter changes at the same speed.

| Parameter | Suggested Polling Rate |
|------------|------------------------|
| Engine RPM | 10 Hz |
| Vehicle Speed | 10 Hz |
| Throttle Position | 10 Hz |
| Engine Load | 5 Hz |
| Mass Air Flow (MAF) | 5 Hz |
| Coolant Temperature | 1 Hz |
| Fuel Level | Every 30–60 seconds |

Using different polling rates reduces unnecessary communication while maintaining responsive real-time monitoring.

---

# Vehicle Compatibility

Not all vehicles support every standardized PID.

DriveVitals should:

1. Connect to the vehicle.
2. Query supported PIDs.
3. Enable only supported telemetry parameters.
4. Gracefully disable unsupported features.

This approach maximizes compatibility across different manufacturers and vehicle models.

---

# Role in DriveVitals

Mode 01 serves as the primary telemetry source for the platform.

The overall data flow is:

```
Vehicle Sensors
      ↓
Engine ECU
      ↓
Mode 01 PID Requests
      ↓
OBD-II Interface
      ↓
ELM327 Adapter
      ↓
Python Backend
      ↓
Telemetry Decoder
      ↓
Analytics Engine
      ↓
Database
      ↓
Real-Time Dashboard
```

---

# Key Takeaways

- Mode 01 provides live telemetry from the ECU.
- DriveVitals relies primarily on Mode 01 for real-time data collection.
- Telemetry values are transmitted in hexadecimal and decoded using OBD-II standard formulas.
- Six core PIDs (RPM, Speed, Coolant Temperature, Engine Load, Throttle Position, and MAF) are sufficient for the first version of DriveVitals.
- Additional PIDs can be incorporated in future releases to support advanced diagnostics, predictive maintenance, and AI-driven analytics.
- The system should dynamically detect supported PIDs to ensure compatibility across different vehicle manufacturers.