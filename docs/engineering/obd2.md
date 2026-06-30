# OBD-II (On-Board Diagnostics II)

## Overview

OBD-II (On-Board Diagnostics II) is a standardized diagnostic interface used in modern vehicles. It allows external devices to communicate with a vehicle's Electronic Control Unit (ECU) to retrieve real-time telemetry, diagnostic information, and vehicle status.

DriveVitals uses OBD-II as the primary source of vehicle telemetry.

---

# Why OBD-II Exists

Before OBD-II, each vehicle manufacturer used its own proprietary diagnostic system, making diagnostics difficult and inconsistent.

OBD-II introduced a universal communication standard that enables diagnostic tools and software to retrieve vehicle data using common commands regardless of the manufacturer.

---

# How DriveVitals Uses OBD-II

DriveVitals collects live telemetry from the vehicle through an ELM327 OBD-II adapter.

The collected data is analyzed to monitor:

- Driver behavior
- Vehicle health
- Fuel efficiency
- Engine performance
- Future predictive maintenance

---

# Communication Flow

```text
Vehicle Sensors
      │
      ▼
 Engine Control Unit (ECU)
      │
      ▼
     CAN Bus
      │
      ▼
   OBD-II Port
      │
      ▼
  ELM327 Adapter
      │
      ▼
 Python Backend
      │
      ▼
 Analytics Engine
      │
      ▼
 PostgreSQL Database
      │
      ▼
 Dashboard
```

---

# OBD-II Modes

OBD-II organizes commands into different operating modes.

| Mode | Purpose | Used in DriveVitals |
|------|----------|---------------------|
| 01 | Current live vehicle data | ✅ Yes |
| 02 | Freeze frame data | Future |
| 03 | Read Diagnostic Trouble Codes (DTCs) | Future |
| 04 | Clear Diagnostic Trouble Codes | No |
| 09 | Vehicle information (VIN, calibration, etc.) | Future |

> **Note:** Version 1 of DriveVitals will primarily use **Mode 01**, since it provides real-time vehicle telemetry.

---

# What is a PID?

A **PID (Parameter ID)** identifies a specific vehicle parameter that can be requested from the ECU.

Common examples:

| PID | Parameter |
|------|-----------|
| 0C | Engine RPM |
| 0D | Vehicle Speed |
| 05 | Engine Coolant Temperature |
| 04 | Calculated Engine Load |
| 11 | Throttle Position |
| 10 | Mass Air Flow (MAF) |

---

# Mode + PID

An OBD-II request is made by combining a **Mode** and a **PID**.

Example request:

```text
01 0C
```

Meaning:

- **Mode 01** → Request current live data
- **PID 0C** → Engine RPM

This command tells the ECU:

> "Send me the vehicle's current engine RPM."

---

# ECU Response

After receiving a request, the ECU returns data in hexadecimal format.

Example:

```text
Request:
01 0C

Response:
41 0C 1A F8
```

The backend decodes this hexadecimal response into a human-readable value before sending it to the analytics engine and dashboard.

---

# Why Hexadecimal?

Vehicle ECUs communicate using binary data. Hexadecimal provides a compact and human-readable representation of this binary information.

Each PID has a predefined decoding formula defined by the OBD-II standard that converts hexadecimal bytes into engineering values such as RPM, temperature, speed, or engine load.

---

# Role of OBD-II in DriveVitals

OBD-II enables DriveVitals to:

- Read live vehicle telemetry
- Monitor engine performance
- Analyze driver behavior
- Calculate fuel efficiency
- Detect abnormal driving events
- Monitor vehicle health
- Collect telemetry for future machine learning models

---

# Key Takeaways

- OBD-II is a standardized diagnostic interface used in modern vehicles.
- It allows external devices to communicate with the ECU.
- DriveVitals uses an ELM327 adapter to access OBD-II data.
- **Mode 01** provides real-time telemetry.
- **PIDs** identify individual vehicle parameters such as RPM, speed, and coolant temperature.
- ECU responses are returned in hexadecimal format and decoded by the backend before analysis.

---

# References

- SAE J1979 – OBD-II Parameter IDs (PIDs)
- ISO 15031 – On-Board Diagnostics Communication
- ELM327 AT Commands Documentation