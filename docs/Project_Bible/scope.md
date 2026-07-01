# Project Scope

DriveVitals is a real-time vehicle telemetry and driver intelligence platform designed for individual vehicle owners, ride-hailing drivers, fleet operators, logistics companies, and automotive service providers. The system bridges the gap between raw vehicle diagnostics and actionable insights by collecting live telemetry data from a vehicle’s Electronic Control Unit (ECU) through the standardized OBD-II interface.

The platform continuously acquires and processes real-time vehicle telemetry, including engine RPM, vehicle speed, throttle position, engine load, coolant temperature, battery voltage, fuel-related parameters, air-fuel ratio, oxygen sensor readings, and other emission-related metrics where supported by the vehicle. This data is analyzed to generate insights into vehicle health, engine performance, fuel efficiency, and driver behavior.

DriveVitals is designed as a **web-based real-time analytics platform**, optimized for fleet monitoring and multi-vehicle intelligence. The system provides a centralized dashboard for visualization, monitoring, and decision-making.

The platform employs a modular architecture consisting of the following core components:

- **Telemetry Acquisition Layer:** Interfaces with the vehicle using an ELM327 OBD-II adapter to collect live sensor data.
- **Backend Processing Layer:** Handles data decoding, normalization, and streaming using a Python-based backend.
- **Analytics Engine:** Applies rule-based logic to detect driving events, evaluate driver behavior, and assess vehicle health.
- **Data Storage Layer:** Stores historical telemetry in PostgreSQL and structured CSV formats for reporting, analysis, and future machine learning use.
- **Web Dashboard:** Provides real-time visualization of vehicle telemetry, driver performance metrics, alerts, trip summaries, and fleet-level analytics.

The initial implementation focuses on rule-based analytics, using predefined engineering thresholds and logical conditions to detect events such as aggressive acceleration, harsh braking, overspeeding, prolonged idling, high engine load, and abnormal vehicle operating conditions. These rules provide transparent and explainable decision-making for real-time insights.

As the system evolves, machine learning models will be integrated to enhance driver behavior classification, anomaly detection, predictive maintenance, and fuel efficiency estimation using historical telemetry data.

The system is designed using a modular, scalable, and extensible architecture, enabling future integration with cloud infrastructure, AI-based decision systems, predictive maintenance modules, and additional automotive intelligence features without requiring major redesign.

## Scope Boundaries

### In-Scope (MVP - Final Year Project Implementation)

- Real-time OBD-II telemetry acquisition using ELM327
- Backend data processing and normalization
- Rule-based driver behavior analysis
- Vehicle health monitoring and alert generation
- Fuel efficiency estimation (MAF/MAP-based)
- Real-time web dashboard for visualization
- Trip history and reporting system
- PostgreSQL-based telemetry storage
- Basic fleet-level monitoring (multi-vehicle support in web dashboard)

### Out-of-Scope (Future Enhancements)

- Native mobile application for drivers
- Machine learning-based driver behavior classification (fully trained models)
- Predictive maintenance using historical ML models
- Computer vision-based driver monitoring (fatigue/distraction detection)
- Cloud-native distributed fleet synchronization
- AI-based driving recommendations and coaching system
- Driver identity recognition and personalization system