# Database Design

## DriveVitals Database Design

**Version:** 1.0
**Project:** DriveVitals – Intelligent Fleet Vehicle Telemetry & Analytics Platform

---

# 1. Purpose

The DriveVitals database is designed to store, organize, and manage vehicle telemetry collected from OBD-II devices (or simulators during development), along with fleet information, trips, analytics, alerts, and vehicle health assessments.

The database serves as the central storage layer of the DriveVitals platform and enables:

* Real-time telemetry ingestion
* Historical trip analysis
* Driver behavior assessment
* Vehicle health monitoring
* Fleet-wide analytics
* Predictive maintenance in future releases

The schema is designed to support both simulated telemetry (Version 1) and real OBD-II hardware (future versions) without structural changes.

---

# 2. Database Design Principles

The database has been designed according to the following principles:

* Modular architecture
* High scalability
* Data normalization
* Minimal redundancy
* Efficient querying
* Easy future extensibility
* Compatibility with PostgreSQL

Raw telemetry is stored separately from processed analytics, allowing the analytics engine to be continuously improved without modifying historical data.

---

# 3. Database Management System

DriveVitals uses **PostgreSQL** as its primary relational database because it provides:

* High reliability
* Excellent indexing capabilities
* Strong ACID compliance
* JSON support
* Time-series friendly querying
* Open-source ecosystem
* Excellent FastAPI integration through SQLAlchemy

---

# 4. Conceptual Database Model

The system is organized around fleets.

Each fleet owns multiple vehicles.

Each vehicle performs multiple trips.

Each trip generates thousands of telemetry records.

Telemetry is processed by the analytics engine to generate alerts, driver scores, and vehicle health summaries.

Conceptual relationship:

Fleet
→ Driver
→ Vehicle
→ Trip
→ Telemetry
→ Analytics

---

# 5. Entity Relationship Overview

## Fleet

Represents an organization operating one or more vehicles.

Examples:

* Logistics company
* Ride-hailing company
* Delivery company
* Automotive service provider

Relationship:

Fleet (1) → (Many) Drivers

Fleet (1) → (Many) Vehicles

---

## Driver

Represents an individual responsible for operating a vehicle.

A driver may operate different vehicles over time.

Relationship:

Driver (1) → (Many) Trips

---

## Vehicle

Represents a physical vehicle within the fleet.

Relationship:

Vehicle (1) → (Many) Trips

---

## Trip

Represents one continuous driving session.

Each trip belongs to:

* One vehicle
* One driver

Each trip contains many telemetry records.

Relationship:

Trip (1) → (Many) Telemetry

Trip (1) → (Many) Alerts

Trip (1) → (One) Driver Score

Trip (1) → (One) Vehicle Health

Trip (1) → (One) Analytics Summary

---

## Telemetry

Stores raw OBD-II readings captured continuously during a trip.

This is expected to become the largest table in the database.

---

## Alerts

Stores events detected by the analytics engine.

Examples include:

* Harsh Braking
* Harsh Acceleration
* Overspeeding
* High Engine Temperature
* High Engine Load

---

## Driver Score

Stores summarized driver behavior metrics for each completed trip.

---

## Vehicle Health

Stores summarized vehicle condition after each trip.

---

## Analytics Summary

Stores aggregated trip-level statistics used by the dashboard.

---

# 6. Logical Database Schema

## fleets

| Column        | Description          |
| ------------- | -------------------- |
| fleet_id (PK) | Fleet identifier     |
| company_name  | Organization name    |
| contact_email | Fleet contact        |
| created_at    | Record creation time |

---

## drivers

| Column         | Description       |
| -------------- | ----------------- |
| driver_id (PK) | Driver identifier |
| fleet_id (FK)  | Associated fleet  |
| full_name      | Driver name       |
| license_number | Driving license   |
| created_at     | Registration date |

---

## vehicles

| Column          | Description                   |
| --------------- | ----------------------------- |
| vehicle_id (PK) | Vehicle identifier            |
| fleet_id (FK)   | Fleet owner                   |
| manufacturer    | Vehicle manufacturer          |
| model           | Vehicle model                 |
| year            | Manufacturing year            |
| fuel_type       | Petrol/Diesel/Hybrid/EV       |
| engine_size     | Engine displacement           |
| vin             | Vehicle Identification Number |
| created_at      | Record creation               |

---

## trips

| Column          | Description        |
| --------------- | ------------------ |
| trip_id (PK)    | Trip identifier    |
| vehicle_id (FK) | Vehicle used       |
| driver_id (FK)  | Driver             |
| start_time      | Trip start         |
| end_time        | Trip end           |
| duration        | Trip duration      |
| distance        | Distance traveled  |
| average_speed   | Average trip speed |
| maximum_speed   | Maximum speed      |

---

## telemetry

| Column              | Description                |
| ------------------- | -------------------------- |
| telemetry_id (PK)   | Reading identifier         |
| trip_id (FK)        | Parent trip                |
| timestamp           | Reading timestamp          |
| rpm                 | Engine RPM                 |
| speed               | Vehicle speed              |
| throttle_position   | Throttle percentage        |
| engine_load         | Engine load                |
| coolant_temperature | Coolant temperature        |
| fuel_rate           | Fuel consumption           |
| gear                | Current gear               |
| battery_voltage     | Battery voltage            |
| maf                 | Mass Air Flow              |
| map                 | Manifold Absolute Pressure |
| fuel_level          | Fuel level                 |
| engine_runtime      | Engine runtime             |

---

## alerts

| Column        | Description               |
| ------------- | ------------------------- |
| alert_id (PK) | Alert identifier          |
| trip_id (FK)  | Parent trip               |
| timestamp     | Alert timestamp           |
| severity      | INFO / WARNING / CRITICAL |
| alert_type    | Alert category            |
| description   | Alert details             |

---

## driver_scores

| Column                    | Description      |
| ------------------------- | ---------------- |
| score_id (PK)             | Score identifier |
| trip_id (FK)              | Parent trip      |
| overall_score             | Driver score     |
| harsh_acceleration_events | Count            |
| harsh_braking_events      | Count            |
| overspeed_events          | Count            |
| idle_time                 | Idle duration    |
| fuel_efficiency_score     | Efficiency score |

---

## vehicle_health

| Column               | Description            |
| -------------------- | ---------------------- |
| health_id (PK)       | Health identifier      |
| trip_id (FK)         | Parent trip            |
| engine_health        | Engine score           |
| battery_health       | Battery score          |
| cooling_health       | Cooling score          |
| overall_health       | Overall vehicle health |
| maintenance_required | Boolean                |

---

## analytics_summary

| Column               | Description          |
| -------------------- | -------------------- |
| summary_id (PK)      | Summary identifier   |
| trip_id (FK)         | Parent trip          |
| average_rpm          | Average RPM          |
| average_speed        | Average speed        |
| fuel_consumed        | Total fuel used      |
| fuel_efficiency      | Overall efficiency   |
| trip_score           | Trip score           |
| driver_score         | Driver score         |
| vehicle_health_score | Vehicle health score |

---

# 7. Relationship Summary

Fleet (1) → (Many) Drivers

Fleet (1) → (Many) Vehicles

Vehicle (1) → (Many) Trips

Driver (1) → (Many) Trips

Trip (1) → (Many) Telemetry

Trip (1) → (Many) Alerts

Trip (1) → (One) Driver Score

Trip (1) → (One) Vehicle Health

Trip (1) → (One) Analytics Summary

---

# 8. Indexing Strategy

The following columns should be indexed for efficient querying:

* fleet_id
* vehicle_id
* driver_id
* trip_id
* timestamp

Telemetry is expected to contain the largest number of records; therefore, timestamp-based indexing is essential for efficient historical analysis.

---

# 9. Scalability Considerations

The database is designed to support:

* Multiple fleets
* Thousands of vehicles
* Millions of telemetry records
* High-frequency telemetry ingestion
* Future cloud deployment
* Horizontal analytics expansion

No schema modifications are required when replacing the simulator with real OBD-II hardware.

---

# 10. Future Extensions

The schema is intentionally extensible for future versions of DriveVitals.

Potential future additions include:

* OBD-II device management
* Supported PID discovery
* Diagnostic Trouble Codes (DTCs)
* GPS route history
* Predictive maintenance records
* AI model predictions
* Driver authentication
* Fleet maintenance scheduling
* Vehicle service history
* Cloud synchronization
* Computer vision driver monitoring

These features can be integrated without redesigning the existing database structure.
