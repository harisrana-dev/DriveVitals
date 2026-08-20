# DriveVitals Documentation

This directory contains technical documentation for the DriveVitals platform. Use this guide to find the information you need.

## Quick Start

- **New to the project?** Start with the main [`README.md`](../README.md) for architecture and overview
- **Integrating with the API?** See [`API.md`](API.md) for REST endpoints and WebSocket contracts
- **Setting up locally?** Check [`../backend/README.md`](../backend/README.md) and [`../frontend/README.md`](../frontend/README.md)
- **Running tests?** See [`TESTING.md`](TESTING.md)

## Core Documentation

| Document | Audience | Purpose |
|----------|----------|---------|
| [`API.md`](API.md) | Backend/Frontend Engineers | Complete REST and WebSocket API reference |
| [`LIMITATIONS.md`](LIMITATIONS.md) | All | Clear separation of implemented, simulated, and planned features |
| [`ANALYTICS.md`](ANALYTICS.md) | Analytics/Backend Engineers | Driver behaviour, vehicle health, scoring, alerts |
| [`TESTING.md`](TESTING.md) | Test Engineers | Test organization, layer breakdown, regression protections |
| [`TELEMETRY.md`](TELEMETRY.md) | Backend Engineers | Telemetry schema, units, flow, simulated vs. real boundary |
| [`TRIP_INTELLIGENCE.md`](TRIP_INTELLIGENCE.md) | Backend/Frontend Engineers | Trip lifecycle, state machine, persistence, WebSocket flow |

## Architecture & Design

### High-Level Architecture

- [`Project_Bible/`](Project_Bible/) — Phase 0 project definition (vision, objectives, scope, constraints, assumptions, roadmap)
- [`design/DigitalTwinArchitecture/`](design/DigitalTwinArchitecture/) — 6-part series on architecture philosophy (master blueprint, object model, simulation engine, vehicle simulation, data flow, deployment)

### Component Design

- [`design/backend/`](design/backend/) — Backend module structure and API design
- [`design/frontend/`](design/frontend/) — Frontend dashboard WebSocket contract
- [`design/database/`](design/database/) — Database schema design and principles
- [`design/analytics_engine/`](design/analytics_engine/) — Analytics pipeline components (behaviour, health, alerts, scoring)

## Engineering Reference

| Document | Purpose |
|----------|---------|
| [`engineering/architecture_specification.md`](engineering/architecture_specification.md) | Comprehensive backend architecture specification |
| [`engineering/vehicle_telemetry.md`](engineering/vehicle_telemetry.md) | Vehicle telemetry signals and ranges |
| [`engineering/obd2.md`](engineering/obd2.md) | OBD-II protocol overview |
| [`engineering/pid_decoding.md`](engineering/pid_decoding.md) | PID value decoding for OBD-II |
| [`engineering/elm327.md`](engineering/elm327.md) | ELM327 serial protocol (groundwork for hardware integration) |
| [`engineering/fuel_&_air_management.md`](engineering/fuel_&_air_management.md) | Engine fuel and air management |
| [`engineering/mode1_&_telemetry_selection.md`](engineering/mode1_&_telemetry_selection.md) | Mode 1 PID selection strategy |
| [`engineering/bitmap_in_obd.md`](engineering/bitmap_in_obd.md) | Bitmap encoding in OBD |
| [`engineering/core_vehicle_telemetry_explained.md`](engineering/core_vehicle_telemetry_explained.md) | Core vehicle telemetry explanation |

## Historical & Reference Documents

| Document | Purpose |
|----------|---------|
| [`DOCUMENTATION_AUDIT.md`](DOCUMENTATION_AUDIT.md) | Previous audit documenting what was outdated and what was fixed |
| [`driver_page_data_contract.md`](driver_page_data_contract.md) | Data contract audit for the Driver page (implementation reference) |
| [`alerts_page_product_ux_audit.md`](alerts_page_product_ux_audit.md) | UX audit findings and recommendations for the Alerts page |

## Research

- [`../research/notes/`](../research/notes/) — Research notes on driver behaviour, fleet telematics, and ML approaches
- [`../research/papers/`](../research/papers/) — Paper summaries and domain knowledge

## Team & Workflow

- [`team/TEAM_WORKFLOW.md`](team/TEAM_WORKFLOW.md) — Team workflow and coordination guidelines

## Key Concepts

### Simulated vs. Real

DriveVitals currently uses **simulated OBD-II-style telemetry** from physics-inspired vehicle models. Real OBD-II / CAN bus integration is planned. See [`LIMITATIONS.md`](LIMITATIONS.md) for details.

### Rule-Based Analytics

All analytics are **100% rule-based and deterministic** (no machine learning in current implementation). Machine learning is a planned roadmap item. See [`ANALYTICS.md`](ANALYTICS.md) for scoring formulas and [`design/analytics_engine/future_ml_integration.md`](design/analytics_engine/future_ml_integration.md) for ML strategy.

### WebSocket Channels

Two independent WebSocket channels:
- `/ws/dashboard` — Live fleet-wide snapshots every tick
- `/ws/trips` — Trip completion and update snapshots

See [`API.md`](API.md) for full details.

### REST API

10 read-only routers covering vehicles, drivers, routes, trips, telemetry, vehicle health, driver statistics, maintenance, alerts, and system status. Alerts router also supports acknowledge and resolve mutations.

See [`API.md`](API.md) for complete reference.

## For Specific Roles

**Recruiter / Admissions Reviewer:**
- Start with [`../README.md`](../README.md) for project scope and technical depth
- Check [`LIMITATIONS.md`](LIMITATIONS.md) for honest scope and design constraints
- No false claims about AI/ML; all future work is clearly marked

**Backend Engineer:**
- [`../backend/README.md`](../backend/README.md) for local setup
- [`API.md`](API.md) for endpoint specs
- [`ANALYTICS.md`](ANALYTICS.md) for engine details
- [`design/DigitalTwinArchitecture/`](design/DigitalTwinArchitecture/) for architectural philosophy

**Frontend Engineer:**
- [`../frontend/README.md`](../frontend/README.md) for local setup
- [`API.md`](API.md) for REST and WebSocket contracts
- [`TRIP_INTELLIGENCE.md`](TRIP_INTELLIGENCE.md) for trip lifecycle

**DevOps / Deployment:**
- `deployment/docker-compose.yml` for database provisioning
- [`design/DigitalTwinArchitecture/06_integration_deployment_architecture.md`](design/DigitalTwinArchitecture/06_integration_deployment_architecture.md) for deployment strategy

**Test Engineer:**
- [`TESTING.md`](TESTING.md) for test organization and critical invariants

## Document Status

All documentation in this directory accurately reflects the current implementation as of August 2026. Historical documents are clearly marked. See [`DOCUMENTATION_AUDIT.md`](DOCUMENTATION_AUDIT.md) for details on what was updated and why.
