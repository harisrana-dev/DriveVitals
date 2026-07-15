# DriveVitals — Data and Intelligence Architecture

Covers the Data Layer and Intelligence Layer from `01-digital-twin-architecture.md`, and fixes **Problem 5 (real vehicle integration must be schema-identical)**.

## 1. Sensor Abstraction Layer

Purpose: decouple *where telemetry comes from* from *everything that consumes it*.

```
Simulation:  Vehicle Physics ──► Virtual Sensor Provider ──► Telemetry Packet
Real:        Vehicle ECU     ──► OBD-II Provider          ──► Telemetry Packet
```

Both providers implement the same interface:

```python
class SensorProvider(Protocol):
    def sample(self, tick_context) -> TelemetryPacket: ...
```

`TelemetryPacket` is a fixed schema (PIDs) regardless of provider:

```
TelemetryPacket {
  vehicle_id, timestamp, source: "simulated" | "obd2"
  speed, rpm, gear, fuel_level
  coolant_temp, engine_load, battery_voltage
  odometer, engine_hours
  fault_codes[]
  stale: bool
  # + 12 additional OBD-II PIDs already defined in the simulator layer
}
```

Everything downstream — Telemetry Pipeline, Analytics Engine, Dashboard — depends only on `TelemetryPacket`, never on whether `source` is `simulated` or `obd2`. This is what makes Problem 5's requirement concrete: swapping a fleet vehicle from a Digital Twin instance to a real OBD-II-connected vehicle requires no changes downstream of the Sensor Abstraction Layer.

## 2. Telemetry Pipeline

Responsibilities:
1. **Ingestion** — receive `TelemetryPacket`s from all active vehicles each tick (or each real-world sample interval for OBD-II sources).
2. **Validation** — schema check, stale-flag propagation, fault-code passthrough.
3. **Fan-out** — three consumers, each on its own cadence:
   - Persistence (every packet, full resolution)
   - Analytics (every packet, incremental)
   - Dashboard (sampled/delta, per `03-simulation-engine-design.md` §4)

## 3. Analytics Engine

Two tiers, matching the scalability design in doc 3:

| Tier | Examples | Cadence |
|---|---|---|
| Fast/cheap (per-tick) | fleet-wide active count, average speed, current fuel efficiency | every tick |
| Slow/expensive (per-trip or windowed) | driver score, vehicle health index, predictive maintenance | trip-end or every N ticks |

### 3.1 Driver Score
Derived from harsh-event counts, adherence to speed limits, fatigue-adjusted behaviour, and fuel efficiency relative to the vehicle's baseline — computed from Trip + Telemetry + Driver data jointly, not from telemetry alone (this is the "relationship-based intelligence" principle from doc 1: the same telemetry means different things for different driver/vehicle/cargo combinations).

### 3.2 Vehicle Health Index
Derived from Physics Engine wear counters (`04-vehicle-simulation-model.md` §4.5) plus fault-code history plus Maintenance's own inspection records.

### 3.3 Fuel Efficiency
Actual fuel burn vs. specification-expected burn under the trip's cargo/route conditions — a relative metric, not absolute L/100km, since raw fuel numbers mean little without route/cargo context.

### 3.4 Predictive Maintenance
ML-readiness note: telemetry + wear + fault history is stored in a schema suitable for training a failure-prediction model later (e.g. time-to-next-fault regression), but the FYP-scope implementation can start as threshold/rule-based prediction, with the schema designed so an ML model can be dropped in without a schema migration.

## 4. Dashboard Requirements

- Fleet overview: active/idle/maintenance-due vehicle counts, live map/positions, alerts.
- Vehicle detail view: live telemetry, health index, current trip, fault codes.
- Driver view: current score, fatigue state, trip history.
- Must remain functional at 500-vehicle scale without re-architecture — this is guaranteed by consuming the same sampled/delta stream described in doc 3, not full-resolution telemetry.

## 5. Data Retention & Access Pattern

- **Hot path**: last N ticks per vehicle, in-memory or fast cache, for dashboard/live queries.
- **Cold path**: full telemetry history in the database, for analytics training and historical reporting (see `06-integration-deployment-architecture.md` for storage choice).

## 6. ML Future Path

Because `TelemetryPacket` and event logs are schema-stable and source-agnostic, models trained on simulated fleet data are directly applicable to real fleet data once real vehicles are integrated — this is the concrete payoff of the abstraction, and worth stating explicitly in an FYP defense or portfolio write-up as the "sim-to-real" argument.