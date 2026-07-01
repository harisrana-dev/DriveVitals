# Bitmap in OBD-II

## What is a Bitmap?

A bitmap is a sequence of **bits (0s and 1s)** where each bit represents the status of something.

- **1** = Supported / Enabled / True
- **0** = Not Supported / Disabled / False

Instead of sending a long list of supported PIDs, the ECU sends a compact bitmap.

---

# Why Use a Bitmap?

Imagine a vehicle supports the following PIDs:

- PID 01
- PID 02
- PID 04
- PID 05

Instead of sending:

```
01
02
04
05
```

The ECU sends one binary number:

```
11011000...
```

Each bit corresponds to one PID.

This is much faster and more efficient.

---

# How OBD-II Uses Bitmaps

When DriveVitals sends:

```
01 00
```

It is asking:

> "Which PIDs from 0x01 to 0x20 do you support?"

The ECU replies:

```
41 00 BE 3F A8 13
```

The last four bytes form a **32-bit bitmap**.

Example:

```
BE = 10111110
```

Each bit represents one PID.

```
Bit:   7 6 5 4 3 2 1 0
Value: 1 0 1 1 1 1 1 0
```

This means:

| Bit | PID | Supported |
|-----|-----|-----------|
| 7 | PID 01 | ✅ |
| 6 | PID 02 | ❌ |
| 5 | PID 03 | ✅ |
| 4 | PID 04 | ✅ |
| 3 | PID 05 | ✅ |
| 2 | PID 06 | ✅ |
| 1 | PID 07 | ✅ |
| 0 | PID 08 | ❌ |

> **Note:** In OBD-II, the most significant bit (leftmost) represents the first PID in the range.

---

# Visual Example

Suppose the bitmap is:

```
11110000
```

This means:

```
PID 01 ✅
PID 02 ✅
PID 03 ✅
PID 04 ✅
PID 05 ❌
PID 06 ❌
PID 07 ❌
PID 08 ❌
```

---

# How DriveVitals Uses It

Startup sequence:

```
Connect to Vehicle
        ↓
Send 01 00
        ↓
Receive Bitmap
        ↓
Decode Supported PIDs
        ↓
Store Supported PID List
        ↓
Only Request Available Telemetry
```

Example:

```
Supported PIDs:

RPM                ✅
Speed              ✅
Throttle Position  ✅
MAF                ❌
Fuel Trim          ❌
Coolant Temp       ✅
```

DriveVitals will only request the supported parameters, making it compatible with different vehicle manufacturers.

---

# Key Takeaways

- A bitmap is a compact way of representing many True/False values.
- In OBD-II, bitmaps are used to advertise which PIDs a vehicle supports.
- The request `01 00` asks for supported PIDs from **0x01–0x20**.
- Each bit corresponds to one PID.
- DriveVitals decodes the bitmap during startup and requests only supported telemetry.