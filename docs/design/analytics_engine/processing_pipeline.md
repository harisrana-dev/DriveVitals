# 2. Analytics Processing Pipeline

## 2.1 Pipeline Overview

The Analytics Engine processes telemetry sequentially through a series of well-defined stages. Each stage performs a specific responsibility and produces standardized outputs for the next stage.

This approach ensures consistent processing, improves maintainability, and simplifies future enhancements.

---

## 2.2 Stage 1 – Telemetry Validation

Incoming telemetry is first validated before analytical processing begins.

The validation stage verifies:

* Required parameters are present.
* Sensor values are within acceptable engineering ranges.
* Data types are valid.
* Timestamps are correctly ordered.
* Corrupted or incomplete records are rejected.

Only validated telemetry proceeds to subsequent stages.

---

## 2.3 Stage 2 – Telemetry Preprocessing

Validated telemetry is standardized before analysis.

Typical preprocessing activities include:

* Unit normalization
* Timestamp synchronization
* Duplicate record removal
* Missing value handling
* Derived metric calculation (where applicable)

The preprocessing stage ensures that all analytical modules operate on consistent, high-quality data.

---

## 2.4 Stage 3 – Analytical Processing

The standardized telemetry stream is evaluated simultaneously by specialized analytical modules.

Each module focuses on a single aspect of vehicle operation:

* Driver Behaviour Analysis
* Vehicle Health Assessment
* Fuel Efficiency Analysis
* Trip Performance Analysis

The analytical modules operate independently, allowing individual components to be modified or extended without affecting the rest of the system.

---

## 2.5 Stage 4 – Alert Generation

Outputs from the analytical modules are evaluated to determine whether predefined engineering rules have been violated.

When a rule is triggered, the Alert Generation Engine creates a corresponding alert containing:

* Rule identifier
* Alert type
* Severity level
* Timestamp
* Associated telemetry values

Alerts are stored for historical analysis and can also be transmitted immediately to the dashboard.

---

## 2.6 Stage 5 – Score Calculation

Following analytical processing, the engine computes summary performance indicators for the completed trip.

The calculated metrics include:

* Driver Score
* Vehicle Health Score
* Fuel Efficiency Score
* Trip Performance Score

These scores provide simplified indicators for comparison across vehicles, drivers, and trips.

---

## 2.7 Stage 6 – Analytics Summary Generation

At the completion of a trip, the engine consolidates all analytical outputs into a structured summary.

The summary includes:

* Driving behaviour statistics
* Vehicle health assessment
* Fuel efficiency metrics
* Generated alerts
* Performance scores
* Trip statistics

The resulting summary is stored in the database and made available through the backend API for visualization and reporting.