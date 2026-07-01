# Fuel & Air Management

## Purpose

Efficient engine operation depends on maintaining the correct balance between air and fuel. Modern Engine Control Units (ECUs) continuously monitor airflow, exhaust gases, and combustion conditions to determine how much fuel should be injected into the engine.

DriveVitals uses these telemetry parameters to estimate fuel efficiency, monitor engine health, detect abnormal operating conditions, and provide intelligent driving insights.

---

# Fuel Combustion Process

A petrol engine operates on a four-stroke cycle:

1. Intake – Air enters the cylinder.
2. Compression – Air-fuel mixture is compressed.
3. Power – The spark plug ignites the mixture, producing power.
4. Exhaust – Burnt gases exit the engine.

For efficient combustion, the ECU must determine the correct amount of fuel to inject based on the amount of incoming air.

---

# Air-Fuel Ratio (AFR)

## What is AFR?

The Air-Fuel Ratio (AFR) represents the ratio of air to fuel entering the engine.

For gasoline engines, the ideal (stoichiometric) ratio is approximately:

```
14.7 : 1
```

Meaning:

- 14.7 kg of air
- 1 kg of fuel

This ratio provides efficient combustion while minimizing fuel consumption and emissions.

---

## Rich vs. Lean Mixture

| Condition | Meaning |
|-----------|---------|
| Rich | Too much fuel, not enough air |
| Lean | Too much air, not enough fuel |
| Stoichiometric | Ideal balance (~14.7:1) |

---

## Why It Matters

Incorrect AFR can result in:

- Increased fuel consumption
- Reduced engine performance
- Higher emissions
- Engine damage if sustained

---

## DriveVitals Usage

- Fuel efficiency estimation
- Combustion analysis
- Engine performance monitoring
- Future machine learning models

---

# Mass Air Flow (MAF) Sensor

## What is MAF?

The Mass Air Flow (MAF) sensor measures the **mass of air entering the engine**, usually expressed in **grams per second (g/s)**.

The ECU uses this value to calculate the amount of fuel required for combustion.

---

## Typical Values

| Driving Condition | Typical MAF |
|-------------------|------------:|
| Idle | 2–5 g/s |
| City Driving | 8–20 g/s |
| Highway Cruising | 15–35 g/s |
| Hard Acceleration | 50–100+ g/s |

*Actual values depend on engine size and design.*

---

## Why It Matters

More air entering the engine requires more fuel.

Higher MAF values generally indicate:

- Higher engine load
- Greater fuel consumption
- Increased engine power output

---

## DriveVitals Usage

- Fuel efficiency estimation
- Airflow monitoring
- Engine performance analysis
- Machine learning feature extraction

---

# Manifold Absolute Pressure (MAP) Sensor

## What is MAP?

Some vehicles do not use a MAF sensor.

Instead, they use a **Manifold Absolute Pressure (MAP)** sensor that measures the air pressure inside the intake manifold.

The ECU estimates airflow using:

- MAP
- Engine RPM
- Intake Air Temperature

---

## MAF vs MAP

| MAF | MAP |
|------|-----|
| Directly measures airflow | Estimates airflow |
| Higher accuracy | Lower cost |
| Common in many modern vehicles | Common in naturally aspirated engines |

DriveVitals should support both methods whenever possible.

---

## DriveVitals Usage

- Airflow estimation
- Fuel efficiency calculations
- Vehicle compatibility

---

# Oxygen (O₂) Sensors

## What are Oxygen Sensors?

Oxygen sensors measure the amount of oxygen remaining in the exhaust gases after combustion.

This information allows the ECU to determine whether the previous combustion cycle was:

- Rich
- Lean
- Near the ideal AFR

The ECU continuously adjusts fuel injection based on this feedback.

---

## Why It Matters

Oxygen sensor data helps maintain:

- Efficient combustion
- Lower emissions
- Stable engine performance

Faulty oxygen sensors can lead to poor fuel economy and incorrect fuel delivery.

---

## DriveVitals Usage

- Engine diagnostics
- Fuel system monitoring
- Combustion efficiency analysis

---

# Fuel Trim

## What is Fuel Trim?

Fuel Trim represents how much the ECU adjusts fuel injection to maintain the desired Air-Fuel Ratio.

Two values are commonly monitored:

- Short-Term Fuel Trim (STFT)
- Long-Term Fuel Trim (LTFT)

---

## Short-Term Fuel Trim (STFT)

STFT represents immediate adjustments made by the ECU based on oxygen sensor feedback.

It changes continuously while the engine is running.

---

## Long-Term Fuel Trim (LTFT)

LTFT represents long-term corrections learned by the ECU over time.

Persistent positive or negative LTFT values may indicate underlying engine or fuel system issues.

---

## Typical Interpretation

| Fuel Trim | Interpretation |
|-----------:|----------------|
| Around 0% | Normal |
| Positive | ECU is adding fuel |
| Negative | ECU is reducing fuel |

Large or persistent corrections may indicate:

- Vacuum leaks
- Dirty injectors
- Sensor faults
- Fuel delivery problems

---

## DriveVitals Usage

- Engine health monitoring
- Fuel system diagnostics
- Predictive maintenance
- Long-term vehicle analytics

---

# Estimating Fuel Efficiency

Most vehicles do not provide direct fuel flow measurements.

Instead, DriveVitals estimates fuel consumption using available telemetry.

---

## Method 1 – MAF-Based Estimation (Preferred)

The estimation process is:

```
Read MAF
        ↓
Estimate Fuel Mass using AFR
        ↓
Convert Fuel Mass to Fuel Volume
        ↓
Combine with Vehicle Speed
        ↓
Estimate Fuel Economy
```

Possible outputs:

- L/100 km
- km/L
- MPG

This method is generally more accurate when MAF data is available.

---

## Method 2 – MAP-Based Estimation

If MAF is unavailable, airflow can be estimated using:

- MAP
- Engine RPM
- Intake Air Temperature
- Engine Displacement
- Estimated Volumetric Efficiency

This approach provides broader compatibility but is less accurate.

---

# Fuel & Air Management Workflow

```
Air enters engine
        ↓
MAF or MAP measures airflow
        ↓
ECU calculates fuel requirement
        ↓
Fuel Injectors deliver fuel
        ↓
Combustion occurs
        ↓
Oxygen Sensor measures exhaust gases
        ↓
Fuel Trim adjusts future injections
```

This closed-loop process repeats continuously while the engine is running.

---

# DriveVitals Feature Mapping

| Parameter | Feature |
|-----------|---------|
| MAF | Fuel Efficiency Estimation |
| MAP | Airflow Estimation |
| Air-Fuel Ratio (AFR) | Combustion Analysis |
| Oxygen Sensors | Engine Diagnostics |
| Short-Term Fuel Trim | Fuel System Monitoring |
| Long-Term Fuel Trim | Predictive Maintenance |

---

# Engineering Considerations

- Not all vehicles support MAF.
- Some vehicles rely entirely on MAP sensors.
- Oxygen sensor support varies between manufacturers.
- Some fuel-related telemetry may only be available through manufacturer-specific PIDs.
- Fuel efficiency calculations are estimates and depend on available telemetry.

---

# Role in DriveVitals

Fuel and air management telemetry enables DriveVitals to move beyond simple diagnostics and provide intelligent insights.

```
Vehicle Sensors
        ↓
ECU
        ↓
OBD-II Telemetry
        ↓
Fuel & Air Analysis
        ↓
Fuel Efficiency Estimation
Engine Health Monitoring
Combustion Analysis
Predictive Maintenance
        ↓
Real-Time Dashboard
```

---

# Key Takeaways

- The ECU determines fuel injection primarily from the amount of air entering the engine.
- The ideal gasoline Air-Fuel Ratio (AFR) is approximately **14.7:1**.
- MAF directly measures incoming air, while MAP estimates airflow.
- Oxygen sensors provide feedback on combustion quality.
- Fuel Trim represents the ECU's corrections to maintain the desired AFR.
- Fuel efficiency can be estimated using MAF-based or MAP-based calculations.
- DriveVitals combines these telemetry parameters to generate fuel economy insights, engine diagnostics, and predictive maintenance recommendations instead of simply displaying raw sensor values.