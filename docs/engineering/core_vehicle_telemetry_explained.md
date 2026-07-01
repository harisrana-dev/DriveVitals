# Understanding Core Vehicle Telemetry

## Purpose

Collecting telemetry from a vehicle is only the first step. The real value comes from understanding what each parameter represents and how multiple parameters can be combined to generate meaningful insights.

DriveVitals does not simply display raw ECU values. Instead, it interprets them to assess driver behavior, vehicle health, fuel efficiency, and engine performance.

---

# 1. Engine RPM (Revolutions Per Minute)

## What is RPM?

Engine RPM (Revolutions Per Minute) represents the number of times the engine's crankshaft rotates in one minute.

It measures **engine rotational speed**, not vehicle speed.

For example:

- 1000 RPM means the crankshaft rotates 1000 times every minute.
- 3000 RPM means the crankshaft rotates 3000 times every minute.

---

## Typical Operating Range

| Driving Condition | Typical RPM |
|-------------------|------------:|
| Engine Off | 0 |
| Idle | 600–900 |
| City Driving | 1500–3000 |
| Highway Cruising | 2000–3500 |
| Hard Acceleration | 3500–6000+ |
| Redline (Vehicle Dependent) | 6000–8000 |

---

## Why It Matters

Higher RPM generally results in:

- Increased fuel consumption
- Greater engine wear
- Higher engine power output

Operating at very low RPM under heavy load can also stress the engine.

---

## DriveVitals Usage

Engine RPM is used for:

- Driver behavior analysis
- Aggressive acceleration detection
- Fuel efficiency estimation
- Engine stress monitoring
- Machine learning feature extraction

---

## Dashboard Visualization

- Live RPM Gauge
- RPM Trend Chart
- High RPM Alerts

---

# 2. Vehicle Speed

## What is Vehicle Speed?

Vehicle speed represents how fast the vehicle is moving, typically measured in kilometers per hour (km/h).

The ECU usually calculates speed using wheel speed sensors or the transmission output speed sensor.

---

## Typical Operating Range

| Driving Condition | Speed |
|-------------------|------:|
| Parked | 0 km/h |
| City Driving | 20–60 km/h |
| Urban Roads | 40–80 km/h |
| Highway | 80–120 km/h |

---

## Why It Matters

Vehicle speed helps determine:

- Driving behavior
- Trip statistics
- Driving efficiency
- Speeding events

Speed becomes significantly more useful when analyzed together with RPM, throttle position, and engine load.

---

## DriveVitals Usage

Vehicle speed is used for:

- Speeding detection
- Trip summaries
- Average speed calculation
- Driver scoring
- Route performance analysis

---

## Dashboard Visualization

- Digital Speedometer
- Speed History Chart
- Trip Statistics

---

# 3. Engine Load

## What is Engine Load?

Engine Load represents how much of the engine's available power is currently being used.

It is expressed as a percentage.

- **0%** → Minimal load
- **100%** → Maximum available load

Engine Load should not be confused with RPM.

---

## Example

| Scenario | RPM | Engine Load |
|----------|----:|------------:|
| Idle | 800 | ~15% |
| Highway Cruise | 2500 | ~35% |
| Climbing a Hill | 2500 | ~90% |
| Hard Acceleration | 4500 | ~100% |

The same RPM can correspond to different engine loads depending on driving conditions.

---

## Why It Matters

High engine load can lead to:

- Increased fuel consumption
- Higher engine temperatures
- Greater mechanical stress

---

## DriveVitals Usage

Engine Load is used for:

- Engine stress analysis
- Fuel efficiency estimation
- Predictive maintenance
- Driver behavior analysis

---

## Dashboard Visualization

- Engine Load Gauge
- Engine Stress Indicator

---

# 4. Throttle Position

## What is Throttle Position?

Throttle Position indicates how far the throttle valve is open.

It reflects the driver's acceleration demand and is expressed as a percentage.

| Throttle Position | Meaning |
|------------------:|---------|
| 0% | Closed |
| 20% | Light Acceleration |
| 50% | Moderate Acceleration |
| 100% | Wide Open Throttle (WOT) |

---

## Why It Matters

Throttle Position directly reflects driver intent.

Rapid increases in throttle position often indicate aggressive driving.

Example:

```
Throttle: 15% → 90%
+
RPM increases rapidly
+
Vehicle speed increases rapidly

↓

Aggressive Acceleration
```

---

## DriveVitals Usage

Throttle Position is used for:

- Driver behavior analysis
- Aggressive acceleration detection
- Fuel efficiency estimation
- Machine learning feature extraction

---

## Dashboard Visualization

- Throttle Position Gauge
- Driver Input Graph

---

# 5. Coolant Temperature

## What is Coolant Temperature?

Coolant Temperature measures the temperature of the engine coolant circulating through the engine.

It provides an indication of the engine's operating temperature.

---

## Typical Operating Range

| Temperature | Condition |
|------------:|-----------|
| Ambient | Cold Engine |
| 80–95°C | Normal Operating Temperature |
| 95–105°C | Heavy Engine Load |
| Above 105°C | High Temperature Warning |
| Above 115°C | Potential Overheating |

*Actual values vary depending on manufacturer and engine design.*

---

## Why It Matters

High coolant temperatures may indicate:

- Heavy engine load
- Cooling system faults
- Low coolant level
- Thermostat or radiator issues

---

## DriveVitals Usage

Coolant Temperature is used for:

- Engine health monitoring
- Overheating detection
- Maintenance recommendations
- Historical temperature analysis

---

## Dashboard Visualization

- Temperature Gauge
- Engine Health Indicator
- Overheating Alerts

---

# 6. Battery / Control Module Voltage

## What is Battery Voltage?

Battery or Control Module Voltage represents the health of the vehicle's electrical charging system.

When the engine is running, the alternator charges the battery.

---

## Typical Operating Range

| Voltage | Interpretation |
|---------:|----------------|
| ~12.6 V | Healthy Battery (Engine Off) |
| 13.5–14.7 V | Normal Charging Voltage |
| Below 12 V | Weak Battery |
| Above 15 V | Charging System Issue |

---

## Why It Matters

Abnormal voltage readings may indicate:

- Weak battery
- Failing alternator
- Electrical system faults

---

## DriveVitals Usage

Battery Voltage is used for:

- Electrical system monitoring
- Maintenance alerts
- Fleet health reporting

---

## Dashboard Visualization

- Voltage Indicator
- Charging System Status

---

# Combining Telemetry

A single telemetry parameter rarely provides enough information to understand vehicle behavior. DriveVitals combines multiple parameters to generate meaningful insights.

| Combined Parameters | Insight |
|---------------------|---------|
| RPM + Throttle Position | Aggressive Acceleration |
| RPM + Vehicle Speed | Driving Efficiency |
| Engine Load + RPM | Engine Stress |
| MAF + Vehicle Speed | Fuel Efficiency |
| Coolant Temperature + Engine Load | Overheating Risk |
| Battery Voltage + RPM | Charging System Health |

This multi-parameter analysis enables DriveVitals to move beyond raw diagnostics and provide intelligent vehicle analytics.

---

# Role in DriveVitals

Core telemetry forms the foundation of the platform.

```
Vehicle Sensors
        ↓
ECU
        ↓
OBD-II Interface
        ↓
Python Backend
        ↓
Telemetry Decoder
        ↓
Analytics Engine
        ↓
Driver Behavior Analysis
Vehicle Health Monitoring
Fuel Efficiency Estimation
Maintenance Prediction
        ↓
Real-Time Dashboard
```

---

# Key Takeaways

- Engine RPM measures engine rotational speed.
- Vehicle Speed measures how fast the vehicle is traveling.
- Engine Load indicates how much of the engine's available power is being used.
- Throttle Position reflects the driver's acceleration demand.
- Coolant Temperature monitors engine thermal health.
- Battery Voltage monitors the electrical charging system.
- Combining multiple telemetry parameters enables intelligent analysis of driver behavior, vehicle health, and fuel efficiency.
- DriveVitals transforms raw ECU telemetry into actionable insights rather than simply displaying sensor values.