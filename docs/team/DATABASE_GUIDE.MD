# Database Guide — DriveVitals

## Technology Stack

| Component | Choice |
|-----------|--------|
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |

---

## Data Models

### Fleet

**Purpose:** Represents a company or group of vehicles managed together.

**Important fields:**
- `id`
- `name`
- `created_at`

**Relationships:**
- Has many `Vehicle`

---

### Vehicle

**Purpose:** Represents a single physical (or simulated) vehicle in a fleet.

**Important fields:**
- `id`
- `fleet_id`
- `vin` (Vehicle Identification Number)
- `make`, `model`, `year`
- `vehicle_type` (e.g. sedan, van, truck)

**Relationships:**
- Belongs to one `Fleet`
- Has many `Trip`
- Has many `Telemetry` records
- Has many `MaintenanceEvent` records

---

### Driver

**Purpose:** Represents a person operating a vehicle.

**Important fields:**
- `id`
- `name`
- `license_number`
- `driver_profile` (e.g. cautious, aggressive, normal)

**Relationships:**
- Has many `Trip`

---

### Trip

**Purpose:** Represents a single journey — from ignition-on to ignition-off.

**Important fields:**
- `id`
- `vehicle_id`
- `driver_id`
- `start_time`, `end_time`
- `distance_km`

**Relationships:**
- Belongs to one `Vehicle`
- Belongs to one `Driver`
- Has many `Telemetry` records
- Has many `AnalyticsSnapshot` records

---

### Telemetry

**Purpose:** Stores **raw vehicle measurements** exactly as reported by the vehicle or simulator — the ground truth.

**Important fields:**
- `id`
- `trip_id`
- `timestamp`
- `speed`, `rpm`, `coolant_temp`, `fuel_level`
- Additional OBD-II PIDs (throttle position, engine load, intake air temp, etc.)

**Relationships:**
- Belongs to one `Trip`
- Belongs to one `Vehicle`

---

### AnalyticsSnapshot

**Purpose:** Stores **calculated insights** derived from telemetry — not raw data.

**Important fields:**
- `id`
- `trip_id`
- `computed_at`
- `fuel_efficiency_score`
- `driver_behavior_score`
- `vehicle_health_score`

**Relationships:**
- Belongs to one `Trip`

---

### Alert

**Purpose:** Represents a notable event that needs attention (e.g. harsh braking, overheating, low fuel).

**Important fields:**
- `id`
- `vehicle_id`
- `alert_type`
- `severity`
- `triggered_at`

**Relationships:**
- Belongs to one `Vehicle`

---

### MaintenanceEvent

**Purpose:** Represents a maintenance action performed or predicted for a vehicle.

**Important fields:**
- `id`
- `vehicle_id`
- `event_type` (e.g. oil change, brake replacement)
- `performed_at` or `predicted_at`
- `notes`

**Relationships:**
- Belongs to one `Vehicle`

---

## Why Telemetry and AnalyticsSnapshot Are Separated

`Telemetry` and `AnalyticsSnapshot` are intentionally two different tables rather than one combined table:

- **Telemetry is immutable ground truth.** It should never be recalculated or overwritten — it's exactly what the vehicle reported.
- **AnalyticsSnapshot is derived and can change.** As the analytics algorithms improve (better fuel efficiency formulas, smarter health scoring), snapshots can be recomputed from historical telemetry without ever touching or risking the raw data.
- This separation also keeps write-heavy telemetry ingestion (high frequency, simple writes) decoupled from read-heavy analytics queries (lower frequency, complex aggregations).

---

## Migrations Workflow (Alembic)

DriveVitals uses Alembic to version-control database schema changes.

### Typical workflow

1. Change a model in `models/` (e.g. add a new field to `Vehicle`)
2. Generate a migration:
   ```bash
   alembic revision --autogenerate -m "add vehicle_type to vehicle table"
   ```
3. **Review the generated migration file** in `migrations/versions/` — autogenerate isn't always perfect
4. Apply the migration:
   ```bash
   alembic upgrade head
   ```
5. Commit both the model change **and** the migration file together in the same PR

### Rules

- Never edit a migration that has already been merged and applied by teammates — create a new migration instead.
- Never modify the database schema by hand outside of Alembic.
- Always pull `develop` and run `alembic upgrade head` after pulling, in case teammates added new migrations.