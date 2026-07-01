# Functional Requirements (FRs)

The following functional requirements define the core capabilities of the DriveVitals system in its initial implementation phase.

---

## 1. Telemetry Acquisition

- The system shall connect to a vehicle using an ELM327 OBD-II adapter.
- The system shall establish communication with the OBD-II interface via Bluetooth or Wi-Fi (depending on adapter type).
- The system shall request and retrieve real-time vehicle telemetry data from the ECU.
- The system shall support standard OBD-II PIDs such as RPM, vehicle speed, coolant temperature, throttle position, engine load, and MAF (where available).

---

## 2. Data Processing

- The system shall decode raw OBD-II responses into human-readable engineering values.
- The system shall normalize telemetry data into a consistent internal format.
- The system shall handle missing or unsupported PIDs gracefully without system failure.
- The system shall timestamp all incoming telemetry data.

---

## 3. Real-Time Monitoring

- The system shall continuously monitor vehicle telemetry in real time.
- The system shall update telemetry values at configurable intervals.
- The system shall detect changes in vehicle state dynamically (e.g., acceleration, idling, braking conditions).

---

## 4. Analytics and Event Detection

- The system shall implement rule-based logic to detect driving events such as:
  - Aggressive acceleration
  - Harsh braking
  - Overspeeding
  - Excessive idling
  - High engine load conditions
- The system shall generate alerts when predefined thresholds are violated.
- The system shall calculate a driver behavior score based on detected events.

---

## 5. Vehicle Health Monitoring

- The system shall monitor engine-related parameters such as:
  - Coolant temperature
  - Battery voltage
  - Fuel trim (if available)
  - Oxygen sensor readings (if available)
- The system shall identify abnormal operating conditions based on threshold rules.
- The system shall generate health warnings when anomalies are detected.

---

## 6. Fuel Efficiency Estimation

- The system shall estimate fuel consumption using available telemetry (MAF-based preferred, MAP-based fallback).
- The system shall calculate fuel efficiency metrics such as L/100 km or km/L.
- The system shall track fuel efficiency over time for trend analysis.

---

## 7. Data Storage

- The system shall store all telemetry data in a structured database (PostgreSQL).
- The system shall support exporting telemetry data in CSV format.
- The system shall store historical trip data for analysis and reporting.

---

## 8. Web Dashboard

- The system shall provide a web-based dashboard for real-time visualization of telemetry data.
- The dashboard shall display live vehicle metrics such as RPM, speed, engine load, and temperature.
- The dashboard shall display driver score and detected events.
- The dashboard shall show trip summaries and historical trends.
- The dashboard shall support multi-vehicle (fleet) monitoring.

---

## 9. Alerts and Notifications

- The system shall generate real-time alerts for detected driving events.
- The system shall display alerts on the web dashboard.
- The system shall categorize alerts based on severity (low, medium, high).

---

## 10. System Extensibility

- The system shall be designed in a modular architecture to support future integration of:
  - Machine learning models
  - Mobile applications
  - Cloud-based data storage
  - Predictive maintenance systems
  - Advanced analytics modules