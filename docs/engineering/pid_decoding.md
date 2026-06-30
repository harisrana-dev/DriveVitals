# OBD-II PID Decoding

## Overview

OBD-II communication works by sending requests to a vehicle's ECU and receiving responses in hexadecimal format. Each request specifies a **Mode** and a **Parameter ID (PID)**. The ECU returns one or more bytes that must be decoded into human-readable engineering values such as RPM, speed, or coolant temperature.

DriveVitals will continuously send PID requests, decode the responses, and use the decoded values for analytics and visualization.

---

# OBD-II Request Structure

An OBD-II request consists of two parts:

- **Mode** – Specifies the type of information being requested.
- **PID (Parameter ID)** – Specifies the exact vehicle parameter.

Example:

```text
01 0C
```

Meaning:

- Mode `01` → Request current live data
- PID `0C` → Engine RPM

This command asks the ECU:

> "Send me the current engine RPM."

---

# ECU Response Structure

The ECU replies with hexadecimal bytes.

Example:

```text
Request:
01 0C

Response:
41 0C 1A F8
```

The response consists of four bytes.

| Byte | Value | Description |
|------|------|-------------|
| Byte 1 | 41 | Response Mode |
| Byte 2 | 0C | PID |
| Byte 3 | 1A | Data Byte A |
| Byte 4 | F8 | Data Byte B |

---

# Response Mode

The ECU confirms a successful request by adding **0x40** to the requested mode.

Formula:

```text
Response Mode = Request Mode + 0x40
```

Examples:

| Request Mode | Response Mode |
|--------------|---------------|
| 01 | 41 |
| 02 | 42 |
| 03 | 43 |
| 09 | 49 |

Therefore,

```text
41
```

means:

> Successful response to Mode 01.

---

# Why Hexadecimal?

Vehicle ECUs communicate using bytes.

Hexadecimal is simply a compact representation of binary data and is widely used in embedded systems because it is easier to read than binary.

Example:

| Hex | Decimal |
|-----|---------|
| 1A | 26 |
| F8 | 248 |
| 46 | 70 |

The backend converts hexadecimal values into engineering values using formulas defined by the OBD-II standard.

---

# Example 1 – Engine RPM

Request:

```text
01 0C
```

Response:

```text
41 0C 1A F8
```

Extract the data bytes:

```text
A = 1A
B = F8
```

Convert to decimal:

```text
A = 26
B = 248
```

RPM Formula:

```text
RPM = ((A × 256) + B) ÷ 4
```

Calculation:

```text
RPM = ((26 × 256) + 248) ÷ 4
RPM = (6656 + 248) ÷ 4
RPM = 6904 ÷ 4
RPM = 1726 RPM
```

Final Result:

> Engine RPM = **1726 RPM**

---

# Example 2 – Vehicle Speed

Request:

```text
01 0D
```

Response:

```text
41 0D 46
```

Extract:

```text
A = 46
```

Convert:

```text
46 (Hex) = 70 (Decimal)
```

Formula:

```text
Speed = A
```

Final Result:

> Vehicle Speed = **70 km/h**

---

# Backend Decoding Pipeline

The backend performs the following steps for every PID request.

```text
Send PID Request
        │
        ▼
Receive Hexadecimal Response
        │
        ▼
Extract Data Bytes
        │
        ▼
Convert Hex → Decimal
        │
        ▼
Apply PID Formula
        │
        ▼
Engineering Value
        │
        ▼
Analytics Engine
        │
        ▼
Dashboard
```

---

# How DriveVitals Uses PID Decoding

DriveVitals will:

- Send OBD-II requests through an ELM327 adapter.
- Receive hexadecimal responses from the ECU.
- Decode each response into engineering values.
- Analyze the decoded telemetry.
- Store telemetry in PostgreSQL.
- Display live values on the dashboard.
- Generate alerts and driver behavior analytics.

---

# Key Takeaways

- Every OBD-II request consists of a Mode and a PID.
- The ECU responds with hexadecimal bytes.
- The response mode equals the request mode plus `0x40`.
- Every PID has its own decoding formula.
- The backend is responsible for converting hexadecimal responses into engineering values.
- Decoded telemetry is the foundation of all DriveVitals analytics.

---

# References

- SAE J1979 – OBD-II Parameter IDs (PIDs)
- ISO 15031 – OBD Communication Standard
- ELM327 Programmer's Manual