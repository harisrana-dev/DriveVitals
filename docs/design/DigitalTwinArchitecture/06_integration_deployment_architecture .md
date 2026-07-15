# DriveVitals — Integration and Deployment Architecture

Covers how the Digital Twin runs as a deployed system and how it will eventually connect to real vehicles.

## 1. Real Vehicle Integration Path

```
Phase 1 (current):  Digital Twin Vehicle Model → Virtual Sensor Provider → Telemetry
Phase 2 (near-term): + OBD-II dongle → OBD-II Provider → Telemetry  (same schema)
Phase 3 (future):    + CAN bus direct read → CAN Provider → Telemetry  (same schema)
```

Because the Sensor Abstraction Layer (`05-data-and-intelligence-architecture.md` §1) fixes the schema, phases 2 and 3 are additive — no changes to Analytics, Dashboard, or Telemetry Pipeline are required when a real provider is added. A single Fleet can mix simulated and real vehicles simultaneously, since the Vehicle Manager treats them identically once telemetry reaches the pipeline.

OBD-II Provider responsibilities:
- Poll standard PIDs (speed, RPM, coolant temp, fuel level, etc.) at a fixed interval over an OBD-II adapter (e.g. ELM327-class hardware, or an existing library).
- Map raw OBD-II PID responses to the same `TelemetryPacket` fields the simulator produces.
- Surface stale/fault conditions the same way the simulator does (real dropped connections map to `stale: true`, not to a fabricated last-known value).

CAN Provider (future) responsibilities: same contract, but reading raw CAN frames and decoding via a DBC file per vehicle model, for lower latency and richer signal access than OBD-II alone.

## 2. Backend Services

| Service | Responsibility |
|---|---|
| Simulation Service | Hosts the Digital Twin Runtime; runs one or more fleet simulations (per `03-simulation-engine-design.md`) |
| Ingestion Service | Receives telemetry (from simulation or real providers) via the Telemetry Pipeline contract |
| Analytics Service | Runs the two-tier analytics described in doc 5 |
| API/Dashboard Backend | Serves the sampled/delta stream to the frontend (WebSocket for live data, REST for historical queries) |
| Dispatch/Fleet Service | Owns Fleet/Dispatch operational state and business logic |

These can start as modules within one process for FYP scope and be split into separate services later without changing their contracts — each already communicates through events/telemetry packets rather than shared memory, which is what makes the split possible later.

## 3. Database & Storage Strategy

| Data | Store | Reasoning |
|---|---|---|
| Operational state (Fleet, Vehicle spec, Driver profile, Dispatch) | Relational DB (e.g. PostgreSQL) | Strong consistency, relational integrity between entities |
| Telemetry history (high-volume, time-series) | Time-series-oriented store or partitioned relational tables | High write throughput at 500-vehicle scale; queries are mostly time-range + vehicle-id |
| Live/hot-path cache | In-memory store (e.g. Redis) | Sub-second dashboard reads without hitting the time-series store per request |
| Events (Trip/Maintenance/Fault) | Relational DB, append-only tables | Auditability, joinable with operational state |

At FYP scope, a single PostgreSQL instance with a properly indexed, partitioned telemetry table is sufficient for 500 vehicles; the schema is designed so a dedicated time-series store can be swapped in later without touching the Ingestion Service's write contract.

## 4. Scaling Strategy (deployment view)

This complements the in-process scaling design in `03-simulation-engine-design.md` §4:

- **Simulation Service** can run multiple fleet instances (e.g. different customer fleets) as separate processes/containers, each independently deterministic per its own `SimulationConfig`.
- **Ingestion Service** scales horizontally behind a queue (e.g. one ingestion worker pool consuming from a message queue fed by the Telemetry Pipeline), decoupling burst load from Analytics/DB write rate.
- **Dashboard Backend** scales horizontally since it only serves sampled/delta data from cache, not from the simulation process directly.

## 5. Why This Matters for the Project's Stated Goals

- **FYP defense**: this document demonstrates the system can be reasoned about independently of implementation — a defensible answer to "how would this actually run in production."
- **Portfolio/Master's applications**: shows explicit sim-to-real design thinking (a recognized theme in automotive/robotics software), not just a simulator.
- **Future product/company page**: the phased OBD-II/CAN integration path is the literal roadmap from "demo" to "real fleet product" without an architecture rewrite.