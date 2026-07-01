# Non-Functional Requirements (NFRs)

The following non-functional requirements define the quality attributes, constraints, and system-wide expectations for DriveVitals.

---

## 1. Performance

- The system shall process and display telemetry data in near real-time with minimal delay.
- The system shall support continuous data streaming with update intervals configurable between 100ms to 1s.
- The analytics engine shall process incoming telemetry without blocking data acquisition.
- The web dashboard shall update live metrics without requiring page refresh.

---

## 2. Scalability

- The system shall support multiple vehicles concurrently in a fleet monitoring setup.
- The backend architecture shall be modular to allow horizontal scaling of telemetry processing and analytics components.
- The system shall be designed to accommodate future cloud-based scaling.

---

## 3. Reliability

- The system shall handle intermittent disconnections from the OBD-II adapter without crashing.
- The system shall recover automatically from temporary communication failures.
- The system shall ensure continuous data logging during active sessions where possible.

---

## 4. Availability

- The web dashboard shall remain accessible during backend runtime.
- The system shall ensure minimal downtime during telemetry processing.
- Critical services (telemetry ingestion and analytics) shall be designed for continuous operation.

---

## 5. Data Accuracy and Integrity

- The system shall ensure accurate decoding of OBD-II PID responses based on standard formulas.
- The system shall validate incoming telemetry data to filter invalid or corrupted readings.
- The system shall maintain consistency between stored data and real-time analytics output.

---

## 6. Maintainability

- The system shall follow a modular architecture separating telemetry, analytics, storage, and presentation layers.
- Codebase shall be structured to allow independent development of backend, analytics engine, and dashboard.
- The system shall support easy updates to rule-based logic without affecting core telemetry acquisition.

---

## 7. Usability

- The web dashboard shall provide a clean, intuitive, and responsive interface.
- The system shall present telemetry data in a human-readable and visually understandable format (charts, gauges, summaries).
- The system shall avoid exposing raw hexadecimal OBD-II data to end users.

---

## 8. Interoperability

- The system shall support standard OBD-II protocols across different vehicle manufacturers.
- The system shall handle variation in supported PIDs between vehicles.
- The system shall be adaptable to both Bluetooth and Wi-Fi based ELM327 devices.

---

## 9. Security (Basic Level for FYP Scope)

- The system shall restrict unauthorized access to fleet data via authentication (if implemented in dashboard).
- The system shall ensure secure handling of telemetry data within the application layer.
- The system shall avoid exposing raw vehicle communication interfaces externally.

---

## 10. Modularity and Extensibility

- The system shall be designed in independent modules for telemetry, analytics, storage, and visualization.
- The architecture shall allow future integration of machine learning models without redesigning the core system.
- The system shall support future expansion into mobile applications and cloud-based services.