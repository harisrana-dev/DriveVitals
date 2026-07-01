# High-Level Architecture

DriveVitals is designed as a modular, layered, and scalable system that transforms raw vehicle telemetry from the OBD-II interface into actionable insights for drivers and fleet operators. The architecture follows a data pipeline approach where each layer is responsible for a specific stage of processing, from data acquisition to visualization and analytics.

---

## 1. System Overview

The system is divided into five main layers:

1. **Data Acquisition Layer**
2. **Telemetry Processing Layer**
3. **Analytics Layer**
4. **Data Storage Layer**
5. **Presentation Layer (Web Dashboard)**

---

## 2. High-Level Architecture Diagram

```
Vehicle Sensors
      ↓
Electronic Control Unit (ECU)
      ↓
OBD-II Interface
      ↓
ELM327 Adapter (Bluetooth / Wi-Fi)
      ↓
Python Telemetry Service
      ↓
Telemetry Processing Layer
      ↓
Analytics Engine (Rule-Based)
      ↓
┌──────────────────────────────┐
│                              │
▼                              ▼
Database (PostgreSQL)     WebSocket/API Layer
│                              │
▼                              ▼
Historical Data           Web Dashboard (Frontend)
                              │
                              ▼
                     Real-Time Visualization
                     Driver Score & Alerts
                     Fleet Analytics
```

---

## 3. Layer Descriptions

### 3.1 Data Acquisition Layer

- Interfaces directly with the vehicle via the OBD-II port.
- Uses an ELM327 adapter as a communication bridge.
- Supports Bluetooth and Wi-Fi connectivity modes.
- Retrieves raw telemetry data using standard OBD-II PIDs.

---

### 3.2 Telemetry Processing Layer

- Implemented in Python using an OBD communication library.
- Sends OBD-II commands (PIDs) to the ELM327 device.
- Receives and decodes hexadecimal ECU responses.
- Converts raw data into structured engineering values.
- Handles missing or unsupported PIDs gracefully.

---

### 3.3 Analytics Layer

- Core intelligence module of DriveVitals.
- Implements rule-based analytics engine.
- Detects driving events such as:
  - Aggressive acceleration
  - Harsh braking
  - Overspeeding
  - Excessive idling
  - Engine stress conditions
- Calculates driver behavior score and vehicle health indicators.
- Prepares data for real-time visualization and storage.

---

### 3.4 Data Storage Layer

- Stores structured telemetry data in PostgreSQL.
- Maintains historical trip records and vehicle sessions.
- Supports CSV export for analysis and machine learning.
- Enables time-series analysis of vehicle behavior.

---

### 3.5 Presentation Layer (Web Dashboard)

- Web-based interface for real-time monitoring and analytics.
- Displays live telemetry such as RPM, speed, coolant temperature, and engine load.
- Shows driver behavior score and detected events.
- Provides fleet-level analytics for multiple vehicles.
- Visualizes historical trends and trip summaries.

---

## 4. Communication Flow

1. Vehicle sensors generate data.
2. ECU processes and exposes data via OBD-II protocol.
3. ELM327 adapter translates OBD-II signals to serial/Wi-Fi communication.
4. Python telemetry service continuously polls vehicle data.
5. Telemetry is decoded and normalized.
6. Analytics engine processes data in real time.
7. Processed data is simultaneously:
   - Stored in the database
   - Sent to the dashboard via WebSocket/API
8. Dashboard visualizes insights for users.

---

## 5. Core Design Principles

### Modular Design
Each system component (telemetry, analytics, storage, UI) is independently developed and replaceable.

### Real-Time Processing
Telemetry is processed in near real-time to enable live monitoring and alerts.

### Scalability
Architecture supports expansion to multiple vehicles (fleet systems) and future cloud deployment.

### Extensibility
Designed to support future integration of:
- Machine Learning models
- Predictive maintenance systems
- Mobile applications
- Cloud analytics platforms

---

## 6. Key System Components Summary

| Component | Responsibility |
|----------|----------------|
| ELM327 Adapter | Hardware communication bridge |
| Telemetry Service | Data acquisition and decoding |
| Analytics Engine | Rule-based intelligence and scoring |
| PostgreSQL Database | Historical data storage |
| WebSocket/API Layer | Real-time communication |
| Web Dashboard | Visualization and user interaction |

---

## 7. Final System View

DriveVitals functions as a real-time data pipeline:

```
Raw Vehicle Data → Telemetry Acquisition → Processing → Analytics → Storage + Visualization
```

This architecture ensures that raw ECU data is transformed into meaningful, actionable intelligence for both individual and fleet-level decision making.