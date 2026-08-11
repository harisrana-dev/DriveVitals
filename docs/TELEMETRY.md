# DriveVitals — Telemetry Documentation

> **Source of truth:** `backend/telemetry/models/telemetry_sample.py`, `backend/telemetry/generators/obd_generator.py`, `backend/fleet/runtime/vehicle_runner.py`.
> This document describes the telemetry as it exists today — simulated, not real OBD-II.

---

## 1. What Telemetry Is

Telemetry in DriveVitals is a **time-stamped set of vehicle measurements** shaped like OBD-II data. Every active vehicle produces one `TelemetrySample` per simulation tick (default: 1 second).

The sample carries **no interpretation** — it is a historical fact, not a conclusion. All analytics, health scoring, and alerting happen downstream.

---

## 2. TelemetrySample Schema

```python
@dataclass(frozen=True)
class TelemetrySample:
    timestamp: datetime
    vehicle_id: str
    driver_id: str
    trip_id: str

    speed_kmh: float
    rpm: float
    throttle_position_percent: float
    brake_pressure: float           # 0.0 .. 1.0
    coolant_temperature_c: float
    engine_load_percent: float
    fuel_rate_lph: float
    fuel_level_percent: float
    odometer_km: float
```

---

## 3. Field Reference

| Field | Unit | Range / Notes | Source |
|-------|------|---------------|--------|
| `timestamp` | ISO-8601 | UTC | Runtime tick clock |
| `vehicle_id` | — | UUID | Fleet assignment |
| `driver_id` | — | UUID | Fleet assignment |
| `trip_id` | — | UUID | Created at runtime startup |
| `speed_kmh` | km/h | 0 .. ~180 (route-limited) | Simulated physics |
| `rpm` | rev/min | ~600 .. ~7000 | Derived from speed, gear, throttle |
| `throttle_position_percent` | % | 0 .. 100 | Driver profile + route |
| `brake_pressure` | 0.0–1.0 | 0 = no brake, 1 = full brake | Driver profile + route |
| `coolant_temperature_c` | °C | ~70 .. ~110 | Engine load + ambient |
| `engine_load_percent` | % | 0 .. 100 | Calculated from throttle, RPM, speed |
| `fuel_rate_lph` | L/h | 0 .. ~35 | Throttle, RPM, engine load |
| `fuel_level_percent` | % | 0 .. 100 | Decremented per tick |
| `odometer_km` | km | Lifetime vehicle distance | Incremented per tick |

---

## 4. Simulated vs. Real Data Boundary

**Today:** All telemetry is produced by `OBDGenerator` inside `VehicleRunner`. The generator uses:

- A seeded random number generator for deterministic behaviour.
- Driver `behavior_profile` (city, highway, aggressive, eco) to shape throttle/brake patterns.
- Route speed limits and geometry to constrain speed and distance.

**Future:** A real OBD-II source (ELM327 / CAN bus) can replace `OBDGenerator` without changing anything downstream of `TelemetryPipeline`, because the pipeline only requires objects that implement the `TelemetryConsumer` protocol and emit `TelemetrySample` instances.

---

## 5. Telemetry Flow

```text
VehicleRunner.tick()
    ↓
OBDGenerator.step()  →  TelemetrySample
    ↓
FleetRunner.tick_all()  collects samples
    ↓
TelemetryPipeline.publish(sample)  [fan-out]
    ↓
    ├─ AnalyticsEngine.consume(sample)
    ├─ PersistenceTelemetryConsumer.consume(sample)
    │     ├─ PersistenceService.persist_telemetry(sample)
    │     ├─ PersistenceService.persist_vehicle_health(health)
    │     └─ PersistenceService.persist_alerts(alerts)
    └─ (future: WebSocket consumer)
```

---

## 6. Telemetry Generation Details

### 6.1 Physics-Inspired Simulation

`OBDGenerator.step()` advances the vehicle by `dt_seconds` (default 1.0 s) and returns:

- A new `TelemetrySample`
- Distance advanced this tick (km)
- Fuel consumed this tick (%)

The generator:

1. Reads the route's current speed limit and the driver's behaviour profile.
2. Computes a target throttle/brake blend.
3. Advances speed, RPM, and position.
4. Derives secondary values (engine load, fuel rate, coolant temperature) from the primary values using heuristic formulas.

### 6.2 Seeded Determinism

Each `VehicleRunner` derives a per-vehicle seed from the simulation `run_id` plus the vehicle's ID hash. This ensures that the same fleet configuration produces the same telemetry sequence across runs.

### 6.3 OBD-II Limitations (Simulated)

The simulator does **not** implement real OBD-II PID decoding. It produces values in the same units and ranges that a real OBD-II adapter would, but:

- No real CAN bus communication.
- No ELM327 AT-command sequence.
- No PID-specific bit parsing.
- No DTC (Diagnostic Trouble Code) generation.

Real OBD-II integration is a roadmap item (see `docs/engineering/elm327.md`, `docs/engineering/obd2.md`).

---

## 7. Persistence

Every telemetry sample is persisted asynchronously by `_PersistenceTelemetryConsumer`, registered inside `DriveVitalsRuntime.run()`:

```python
asyncio.ensure_future(
    self._svc.persist_telemetry(sample)
)
```

The database column `brake_percent` stores `brake_pressure * 100` (rounded to 2 decimal places), converting the internal 0–1 representation to a percentage.

Telemetry samples are written in the order they are produced, one database transaction per sample.

---

## 8. Update Cadence

| Source | Cadence |
|--------|---------|
| VehicleRunner tick | 1 Hz per active vehicle |
| TelemetryPipeline publish | Synchronous, same tick |
| Persistence (telemetry samples) | Async, per sample |
| Persistence (health snapshots) | Async, per sample (if health exists) |
| Dashboard WebSocket broadcast | Async, per AnalyticsSnapshot (~1 Hz per vehicle) |
| Trips WebSocket broadcast | Per tick (active trips) + per completion |

---

## 9. Key Invariants

1. **One sample per vehicle per tick.** `FleetRunner.tick_all()` returns exactly one `TelemetrySample` for each active vehicle.
2. **Samples are immutable.** `TelemetrySample` is a frozen dataclass.
3. **Trip FK ordering.** Trip rows are created before any telemetry is produced, satisfying the `telemetry_samples_trip_id_fkey` constraint.
4. **No fabricated telemetry.** `TelemetrySample` fields are always derived from the simulator or, in the future, from real OBD-II reads. No field is invented after the fact.
