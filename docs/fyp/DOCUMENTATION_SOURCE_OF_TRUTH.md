# DriveVitals — Documentation Source of Truth (DST)

> Forensic extraction of the implemented system. **This document precedes and constrains Chapters 1–5.**
> Every statement below is traced to repository evidence. Nothing here is aspirational.

---

# DriveVitals — Documentation Source of Truth (DST)

> Forensic extraction of the implemented system. **This document precedes and constrains Chapters 1–5.**
> Every statement below is traced to repository evidence. Nothing here is aspirational.

---

## 1. Document Metadata

| Field | Value |
|---|---|
| Artifact | Documentation Source of Truth (DST) |
| Purpose | Single factual foundation for FYP Chapters 1–5 |
| Repository | `https://github.com/harisrana-dev/DriveVitals.git` |
| Branch | `feat/m5.3-final-release-verification` |
| Commit | `b8864f21eccbd5a5a4fb373c7b5792830f7a47f5` (`b8864f2`) |
| Base | `fc2e63b` (M5.2) ← `dcab526` (M5.1) ← `6d57e7b` (`develop`, untouched) |
| Engineering status | Feature-frozen; M5.3 final release verification complete |
| Working tree | Clean except untracked `docs/fyp/` (existing FYP working files, not modified) |
| Extraction basis | Direct inspection of code, live database, live API, test suites, Git history |
| Chapters written | **None.** This is the extraction stage only. |

### 1.1 Existing FYP material inspected

| File | Role | Notes |
|---|---|---|
| `docs/fyp/DriveVitals_FYP_Report.docx` | Draft 0.1 report | Front matter + Chapter 1 only (generated 26 Sep 2026) |
| `docs/fyp/DriveVitals_Document_Generation_Report.md` | Engineering/audit note | Contains one claim now falsified — see §28, row **C-06** |
| `docs/fyp/generate_report.py` | python-docx generator | Source of the Draft 0.1 text |
| `docs/fyp/~$iveVitals_FYP_Report.docx` | Word lock file | Editor artefact, 162 bytes, untracked |

No existing FYP file was modified or overwritten by this extraction.

---

## 2. Evidence Hierarchy Applied

Where sources disagreed, the higher-ranked source won. Ranks used throughout:

| Rank | Source | How it was used in this extraction |
|---|---|---|
| 1 | **Verified runtime behaviour** | Live API + real console-interrupt shutdown + simulation timing measurements |
| 2 | **Automated tests** | 525 backend / 265 frontend tests as executable specification |
| 3 | Current implementation | Source read line-by-line for architecture and algorithms |
| 4 | Database schema / migrations | Live `information_schema` queries + fresh-database migration replay |
| 5 | API schemas / contracts | OpenAPI inventory generated from the running app |
| 6 | Frontend behaviour | Source + Vitest suites |
| 7 | Architecture / configuration | Compose, Dockerfiles, CI workflow, package manifests |
| 8 | README / `docs/` | Audited, corrected in M5.3, re-audited here |
| 9 | Historical docs / proposals | Recorded as history, **never** as current fact |
| 10 | Assumptions / inference | Labelled `UNVERIFIED`; excluded from fact tables |

---

## 3. Project Identity

### 3.1 Title

| Status | Title | Source |
|---|---|---|
| **CURRENT** | **DriveVitals** | `README.md` line 1; package name `drivevitals` in `frontend/package.json` |
| HISTORICAL | "DriveVitals — Fleet Intelligence and Digital Twin Platform" | `README.md` subtitle wording; same product, marketing-expanded form |
| UNRESOLVED | Official university-registered title | Not recorded anywhere in the repository — see §38 |

### 3.2 Project area

**Primary:** Real-Time Fleet Intelligence / Vehicle Telematics Analytics.
**Secondary:** Digital Twin Systems (simulation control plane); Rule-Based Automotive Analytics.

Explicitly **not** an AI/ML project: the codebase contains no trained model, no
inference, no dataset, and no ML dependency. See §37 (Do Not Claim).

### 3.3 One-sentence system definition

> DriveVitals is a FastAPI/React web application that runs a controlled synthetic vehicle-fleet simulation ("Digital Twin"), generates OBD-II-shaped telemetry from a seeded physics-style generator, applies deterministic rule-based analytics for driver behaviour, vehicle health, maintenance estimation and alerting, persists the results to PostgreSQL, and streams live fleet state to a browser dashboard over authenticated WebSocket connections.

### 3.4 Problem, solution, motivation, future


---

## 4. System Boundary

### 4.1 Inside the boundary (verified in code)

| Capability | Evidence |
|---|---|
| Authentication (signup, login, logout, session identity) | `backend/api/v1/routers/auth.py`, `backend/api/security.py`, `tests/api/test_auth.py` |
| Role-based authorization (viewer / operator / admin) | `backend/api/v1/dependencies.py::require_role`, `tests/api/test_authorization.py`, `tests/api/test_authorization_perimeter.py` |
| Fleet entity management (drivers, vehicles, routes, assignments) | `backend/api/v1/routers/digital_twin.py`, `backend/db/models/` |
| Scenario configuration (seed, speed, duration, assignment sets) | `backend/api/v1/schemas/digital_twin.py`, `backend/db/models/scenario.py` |
| Simulation lifecycle (activate, launch, stop, run history, reset) | `backend/application/simulation_controller.py` |
| Synthetic telemetry generation | `backend/telemetry/generators/obd_generator.py::OBDGenerator` |
| Driver behaviour analytics | `backend/analytics/behaviour/` |
| Vehicle health analytics (5 subsystems) | `backend/analytics/vehicle_health/` |
| Driver statistics + canonical safety score | `backend/analytics/driver_statistics/` |
| Maintenance estimation | `backend/maintenance/` |
| Alert generation, deduplication, resolution | `backend/alerts/` |
| Persistence + stale-trip recovery + migration | `backend/db/persistence_service.py`, `backend/db/migrations/` |
| REST API (14 routers, 74 operations) | `backend/api/v1/` |
| Authenticated WebSocket channels (3) | `backend/api/websocket/` |
| React dashboard with live updates | `frontend/src/pages/`, `frontend/src/context/LiveDataContext.jsx` |
| Admin settings control plane | `backend/api/v1/routers/settings.py`, `frontend/src/pages/Settings.jsx` |

### 4.2 Outside the boundary (explicitly not implemented)

| Excluded | Verification |
|---|---|
| Real CAN bus ingestion | No CAN/OBD adapter exists; `OBDGenerator` is the only telemetry source |
| ELM327 / OBD-II hardware | `docs/engineering/` holds OBD-II *reference* material only; nothing is wired |
| Physical vehicle sensors / ECU | No hardware integration code anywhere |
| Machine learning / AI models | No ML dependency in `requirements.txt`; analytics are deterministic and threshold-driven |
| Cloud deployment, multi-tenancy | Compose is a local 4-service stack; no cloud manifests, no tenant isolation |
| Message broker / cache / task queue | No Redis, Kafka, Celery, or equivalent (`README.md` line 274 and dependency absence) |
| Microservice decomposition | Single Python process, in-process modules |

---

## 5. Scope

### IN SCOPE
Controlled synthetic fleet simulation with configurable, reproducible scenarios; rule-based analytics (driver behaviour, vehicle health, maintenance estimation, alerting, trip metrics); persistence of telemetry, trips, events, statistics, health, maintenance, alerts, scenarios, runs, users, sessions and settings; REST + WebSocket delivery to a React dashboard; three-role access control with session authentication; admin control plane for simulation fixtures, scenarios and system settings; automated test suites and an Alembic-migrated schema.

### OUT OF SCOPE
Real hardware ingestion; ML/AI; cloud/multi-tenant operation; message brokers; report/export; external identity providers; route optimisation; production fleet operations.

### PARTIALLY IMPLEMENTED
| Area | Implemented | Gap |
|---|---|---|
| Fuel accounting | Persisted trip fuel from per-vehicle `tank_capacity_liters` | Dashboard *live* fuel estimate uses a fixed 60 L constant (`backend/dashboard/services/dashboard_builder.py`) |
| Simulation speed | `simulation_speed` sets the tick interval | Achieved rate slightly below requested (measured 8.6× for a 10× setting) |
| Telemetry freshness | Live + persisted data | Frontend adapters render `0` when a live signal is absent |
| Vehicle lifetime statistics | `vehicle_statistics` table exists | Never written or read; 0 rows |

### FUTURE POSSIBILITY
Physical OBD-II ingestion; ML scoring; predictive maintenance; rolling-window anomaly detection; reports/export; cloud deployment; external identity providers. All are **documented intentions only**, with no code.

---

## 6. Delimitations

1. **Simulation-only telemetry.** No claim about real vehicle accuracy is permissible.
2. **Single-process runtime.** One asyncio event loop per backend process; in-memory analytics state is lost on restart and rebuilt.
3. **Local deployment.** Docker Compose and local Python/Node are the supported runtimes.
4. **Rule-based analytics only.** Every score, flag and recommendation is deterministic and threshold-driven.
5. **Demonstrative purpose.** `README.md` §Current Scope & Limitations: "Project demo only … not intended for production use, commercial deployment, or operational fleet management."
6. **Fleet fixture size.** The default fixture fleet is 6 vehicles / 6 drivers / 6 routes / 6 assignments (`backend/fleet/config/fleet_config.py`).

---

## 7. Assumptions (verified as required by the implementation)

| ID | Assumption | Why required | Verification |
|---|---|---|---|

---

## 8. Constraints

| ID | Type | Constraint | Evidence |
|---|---|---|---|
| C-S1 | SYSTEM | Single-process asyncio runtime; no horizontal scaling, load balancing or caching | `backend/README.md` §Limitations; one `DriveVitalsRuntime` |
| C-S2 | SYSTEM | In-memory analytics state is not shared across restarts | `backend/analytics/state/`, `backend/analytics/context/` |

---

## 9. Actors

Human/role actors only. Internal components (§17–22) are **system components**,
not UML actors, and must not be drawn as actors in the use-case diagram.

| Actor | Type | Responsibilities | Verified capabilities |
|---|---|---|---|
| **Anonymous visitor** | Human (unauthenticated) | Public inspection | `GET /`, `/api/v1/system/health|version|status`, and the fleet/analytics read surface (vehicles, drivers, routes, trips, telemetry, vehicle-health, driver-statistics, maintenance, alerts, analytics) → `200`. Cannot use `/auth/me`, any mutation, Settings or Digital Twin → `401`/`403`. Policy enforced by `tests/api/test_authorization_perimeter.py::ANONYMOUS_READS`. |
| **Viewer** | Human (authenticated, `viewer`) | Read-only monitoring | All anonymous reads **plus** `GET /auth/me`. Cannot mutate. |
| **Operator** | Human (authenticated, `operator`) | Day-to-day fleet administration | Viewer capabilities plus: acknowledge/resolve alerts (`backend/api/v1/routers/alerts.py:247,269`), complete maintenance (`maintenance.py:156`), delete trips and purge aborted trips (`trips.py:104,124`). |
| **Administrator** | Human (authenticated, `admin`) | System and simulation administration | Operator capabilities plus: all `/api/v1/settings*` routes, read **and** write (`settings.py:40,57,83`), and the entire Digital Twin control plane — 28 admin-guarded routes (`digital_twin.py`). |
| **Bootstrap operator** | System process (one-time) | Creates the first administrator when the users table is empty | `backend/api/v1/services/admin_bootstrap.py`; requires all three `BOOTSTRAP_ADMIN_*` variables together; never alters existing users |

---

## 10. Authentication and Authorization

### 10.1 Authentication flow

1. **Credentials exchange** — `POST /api/v1/auth/signup` or `/login` (public routes).
2. **Password storage** — scrypt hashing (`backend/api/security.py::ScryptPasswordHasher`); plaintext is never persisted.
3. **Token issuance** — an opaque random token is returned; only its **SHA-256 hash** is stored (`auth_sessions.token_hash`, unique index `ix_auth_sessions_token_hash`).
4. **Request authentication** — `Authorization: Bearer <token>`; `get_current_user` resolves the session, checks expiry/revocation and rejects inactive users.
5. **Session lifetime** — `ACCESS_TOKEN_TTL_HOURS`, default 24 (`.env.example`); stored in `auth_sessions.expires_at` / `revoked_at`.
6. **Logout** — `POST /auth/logout` sets `revoked_at`; the token stops working immediately for new requests.
7. **Session identity** — `GET /auth/me` returns profile, role and expiry.
8. **Bootstrap** — the first administrator is provisioned once from `BOOTSTRAP_ADMIN_EMAIL/PASSWORD/NAME`.

Evidence: `backend/api/v1/services/auth_service.py`, `backend/api/v1/routers/auth.py`, `backend/db/models/auth_session.py`, `tests/api/test_auth.py`, `tests/api/test_bootstrap_admin.py`.

### 10.2 Authorization flow

- `require_role("admin")` → `require_admin`; `require_role("operator","admin")` → `require_operator_or_admin` (`backend/api/v1/dependencies.py:170-198`).
- Unauthenticated → `401 INVALID_OR_EXPIRED_TOKEN`; authenticated but insufficient role → `403 INSUFFICIENT_PERMISSIONS` (**never** a 401).
- The guard exposes `__authz_roles__` so route guards are introspectable by tests.

### 10.3 Role matrix (verified against router dependencies)

| Surface | Anonymous | Viewer | Operator | Admin |
|---|---|---|---|---|
| Fleet/analytics reads, system health/version/status, `/` | 200 | yes | yes | yes |
| `GET /auth/me` | 401 | yes | yes | yes |
| Alert acknowledge / resolve | 401 | 403 | yes | yes |
| Maintenance complete | 401 | 403 | yes | yes |
| Trip delete / delete aborted | 401 | 403 | yes | yes |
| Settings read **and** write | 401 | 403 | 403 | yes |
| Digital Twin (28 routes incl. launch/stop/reset) | 401 | 403 | 403 | yes |
| WebSocket channels | close 4401 | yes | yes | yes |

### 10.4 Anonymous-read policy — intentional, not a defect

The fleet read surface is deliberately anonymous. This is a **designed exposure
policy**, enforced by a regression test that fails if any new route is not
explicitly classified (`tests/api/test_authorization_perimeter.py`). Its stated
rationale is that these routes "expose operational data only — never
configuration". This DST records it as an implementation fact and **forbids**
describing it as an authorization defect in any chapter.

### 10.5 WebSocket security model

- Token supplied as `?token=` query parameter (`backend/api/websocket/security.py::authenticate_ws`).
- Missing / invalid / expired / revoked token, or inactive user → handshake closed with **code 4401**, reason `Unauthenticated: missing, invalid or expired session token`.
- The check runs **once at connect time**; logout does not terminate already-open sockets (constraint C-S5).
- All three channels require the token: `/ws/dashboard`, `/ws/trips`, `/ws/alerts`.

### 10.6 Frontend route protection

`frontend/src/App.jsx` nests every application page under `<ProtectedRoute>`, and Settings + Digital Twin Lab under `<RoleRoute roles={['admin']}>`. Unauthenticated access redirects to `/login`; an unauthorised role renders the `Unauthorized` page. Evidence: `frontend/src/components/auth/ProtectedRoute.jsx`, `RoleRoute.jsx`, `frontend/src/context/AuthContext.jsx`, `frontend/src/pages/Unauthorized.jsx`, `ProtectedRoute.test.jsx`, `RoleRoute.test.jsx`.

| A-01 | Synthetic telemetry is acceptable input for the analytics pipeline | `OBDGenerator` is the sole producer; analytics consumes `TelemetrySample` objects with no physical-source coupling | `backend/telemetry/generators/obd_generator.py` |
| A-02 | PostgreSQL is available and configured via environment | Every repository uses `AsyncSession` over asyncpg; Alembic requires `POSTGRES_*` | `backend/db/session.py` fails loudly without `POSTGRES_PASSWORD` |
| A-03 | A single application runtime owns the simulation | `DriveVitalsRuntime` holds one fleet, one analytics engine, one controller | `backend/application/runtime.py` |
| A-04 | Users operate through the three defined roles | `users.role` is a DB enum; every mutation/control-plane route declares a role | `user_role` enum in the live database; `require_role` |
| A-05 | Tests run against a dedicated `*_test` database | API tests drop and recreate the schema per test | `tests/api/conftest.py` refuses a non-`*_test` DSN |
| A-06 | Browser WS clients pass the session token as a query parameter | Browsers cannot set headers on a WebSocket handshake | `backend/api/websocket/security.py` |

---

## 11. Functional Requirements

Status key: **Implemented** (code + test evidence) · **Partial** (implemented with a documented gap). Nothing aspirational is listed as a requirement.

### 11.1 Authentication and authorization

| ID | Requirement | Actor | Evidence | Test | Status |
|---|---|---|---|---|---|
| FR-AUTH-01 | The system shall authenticate a user by email and password | All | `backend/api/v1/services/auth_service.py::login` | `tests/api/test_auth.py` | Implemented |
| FR-AUTH-02 | Passwords shall be stored as scrypt hashes, never in plaintext | Admin | `backend/api/security.py::ScryptPasswordHasher` | `tests/api/test_auth.py` | Implemented |
| FR-AUTH-03 | The system shall issue an opaque bearer token and store only its SHA-256 hash | All | `backend/api/security.py::generate_token/hash_token` | `tests/api/test_auth.py` | Implemented |
| FR-AUTH-04 | A registered user shall be able to log out, revoking the session immediately | All | `auth_service.py::logout` → `auth_sessions.revoked_at` | `tests/api/test_auth.py` | Implemented |
| FR-AUTH-05 | The system shall return the current identity, role and session expiry | Authenticated | `GET /api/v1/auth/me` | `tests/api/test_auth.py` | Implemented |
| FR-AUTH-06 | Expired, revoked or invalid tokens shall be rejected with 401 | Anonymous | `backend/api/v1/dependencies.py::get_current_user` | `tests/api/test_auth.py` | Implemented |
| FR-AUTH-07 | Unauthenticated requests to protected endpoints shall be rejected with 401 | Anonymous | `require_role` → `get_current_user` | `tests/api/test_authorization_perimeter.py` | Implemented |
| FR-AUTH-08 | A first administrator shall be created once from environment configuration when no users exist | Bootstrap | `backend/api/v1/services/admin_bootstrap.py` | `tests/api/test_bootstrap_admin.py` | Implemented |
| FR-RBAC-01 | The system shall enforce exactly three roles: admin, operator, viewer | All | `user_role` PostgreSQL enum; `require_admin` / `require_operator_or_admin` | `tests/api/test_authorization.py` | Implemented |

### 11.2 Fleet domain and Digital Twin control plane

| ID | Requirement | Actor | Evidence | Test | Status |
|---|---|---|---|---|---|
| FR-DRV-01 | The system shall create, list, update and delete drivers | Admin | `digital_twin.py` driver routes | `tests/api/test_digital_twin.py` | Implemented |
| FR-DRV-02 | Driver licence numbers shall be unique | Admin | unique index `ix_drivers_license_number` | `test_duplicate_driver_licence_returns_409` | Implemented |
| FR-VEH-01 | The system shall create, list, update and delete vehicles with configurable simulation parameters | Admin | `digital_twin.py` vehicle routes | `tests/api/test_digital_twin.py` | Implemented |
| FR-VEH-02 | A unique-value collision shall return 409, never 500 | Admin | `digital_twin_service.py::_translates_conflicts` | `test_duplicate_vehicle_vin_returns_409_not_500` | Implemented |
| FR-ROUTE-01 | The system shall create, list, update and delete routes | Admin | `digital_twin.py` route routes | `tests/api/test_digital_twin.py` | Implemented |
| FR-ASSIGN-01 | The system shall manage driver/vehicle/route assignments | Admin | `digital_twin.py` assignment routes | `tests/api/test_digital_twin.py` | Implemented |
| FR-ASSIGN-02 | The (driver, vehicle, route) triple shall be unique | Admin | `uq_assignments_driver_vehicle_route` | `test_assignment_crud` | Implemented |
| FR-SCN-01 | The system shall create scenarios with name, seed, simulation speed and duration | Admin | `backend/db/models/scenario.py` | `tests/unit/test_scenario_parameters.py` | Implemented |
| FR-SCN-02 | A scenario shall persist its assignment set via an association table | Admin | `scenario_assignments` | `tests/integration/test_scenario_assignments.py` | Implemented |
| FR-SCN-03 | A running scenario shall reject edits | Admin | `digital_twin_service.py::update_scenario` → 409 | `tests/api/test_digital_twin.py` | Implemented |
| FR-SIM-01 | The system shall launch a scenario and return a run identifier | Admin | launch route → `SimulationController.launch` | `tests/integration/test_simulation_controller.py` | Implemented |
| FR-SIM-02 | The system shall stop a running simulation and persist the run outcome | Admin | `SimulationController.stop` | `tests/integration/test_simulation_controller.py` | Implemented |
| FR-SIM-03 | A configured duration shall terminate the run automatically | Admin | `backend/application/runtime.py` duration branch | `tests/integration/test_simulation_controller.py` | Implemented |
| FR-SIM-04 | A scenario seed shall reproduce the same telemetry sequence across runs | Admin | `runtime.py` seeds every vehicle generator | `tests/unit/test_scenario_parameters.py` + M5.3 acceptance | Implemented |
| FR-SIM-05 | `simulation_speed` shall change the rate simulated time advances | Admin | `runtime.py` sleeps `tick_seconds / speed` | M5.3 acceptance (8.6× measured) | Implemented |
| FR-SIM-06 | Only one run may be active at a time | Admin | `SimulationController` single-run guard | `tests/integration/test_simulation_controller.py` | Implemented |

### 11.3 Telemetry, analytics and alerting

| ID | Requirement | Actor | Evidence | Test | Status |
|---|---|---|---|---|---|
| FR-TEL-01 | The simulator shall generate one telemetry sample per vehicle per tick | System | `VehicleRunner.tick` → `OBDGenerator.step` | `tests/unit/test_vehicle_runner_peak_speed.py` | Implemented |
| FR-TEL-02 | Telemetry shall be persisted per tick with `brake_pressure` (0–1) converted to `brake_percent` (0–100) | System | `TelemetryRepository.insert`, `PersistenceService.persist_telemetry` | `tests/integration/test_telemetry_brake_percent.py` | Implemented |
| FR-TEL-03 | Telemetry shall be queryable by vehicle and by trip | Any reader | `backend/api/v1/routers/telemetry.py` | `tests/api/test_telemetry.py` | Implemented |
| FR-ANL-01 | The system shall detect speeding, harsh braking, aggressive throttle and high RPM | System | `analytics/behaviour/detection/analyzer.py` thresholds | `tests/unit/test_analytics_engine.py` | Implemented |
| FR-ANL-02 | The system shall assign severity (normal/minor/moderate/severe) to behaviour events | System | `analytics/behaviour/events/tracker.py` | `tests/unit/test_analytics_engine.py` | Implemented |
| FR-ANL-03 | The system shall compute one canonical safety score normalised by distance | System | `analytics/driver_statistics/safety.py::compute_safety_score` | `tests/unit/test_safety_scoring.py`, `test_safety_score_sources.py` | Implemented |
| FR-ANL-04 | The system shall map a safety score to a letter grade A–F | System | `safety.py::compute_grade` | `tests/unit/test_safety_scoring.py` | Implemented |
| FR-ANL-05 | The system shall score vehicle health across five subsystems and aggregate them with configured weights | System | `analytics/vehicle_health/` | `tests/unit/test_health_reasons.py` | Implemented |
| FR-ANL-06 | Unknown health shall persist as NULL, never as a fabricated perfect score | System | migration `b7d1f3a9c2e5` | `test_health_reasons.py` + live schema check | Implemented |
| FR-ANL-07 | The system shall estimate maintenance recommendations per component with priority and due odometer | System | `backend/maintenance/estimators/` | `tests/integration/test_intelligence_persistence.py` | Implemented |
| FR-ANL-08 | The system shall expose fleet, vehicle, driver, trip and event analytics | Any reader | `backend/api/v1/routers/analytics.py` | `tests/test_analytics_api.py` | Implemented |
| FR-ALT-01 | The system shall raise alerts from telemetry, trip, health and maintenance conditions | System | `backend/alerts/generators/` | `tests/integration/test_alert_lifecycle.py` | Implemented |
| FR-ALT-02 | Duplicate alerts shall be suppressed and cleared alerts auto-resolved | System | `backend/alerts/deduplication.py`, `resolve_cleared_alerts` | `tests/integration/test_alert_lifecycle.py` | Implemented |
| FR-ALT-03 | Concurrent alert writes shall remain consistent | System | `PersistenceService` alert write lock | `tests/integration/test_alert_concurrency.py` | Implemented |
| FR-ALT-04 | An operator shall acknowledge and resolve an alert | Operator | `alerts.py:247,269` | `tests/api/test_alerts.py` | Implemented |

### 11.4 Delivery, dashboard and administration

| ID | Requirement | Actor | Evidence | Test | Status |
|---|---|---|---|---|---|
| FR-WS-01 | The system shall push fleet snapshots on `/ws/dashboard` | Authenticated | `backend/api/websocket/dashboard.py`, `snapshot_publisher.py` | `tests/api/test_websockets.py` | Implemented |

---

## 12. Non-Functional Requirements

Only measured or directly evidenced statements appear here. Where a threshold was never specified or measured, the entry says **NOT QUANTIFIED** rather than inventing a number.

| ID | Category | Requirement | Measurement / Evidence | Status |
|---|---|---|---|---|
| NFR-SEC-01 | Security | Passwords shall never be stored or logged in plaintext | scrypt hashing in `backend/api/security.py`; credential scan of the tracked tree found no secrets | Implemented |
| NFR-SEC-02 | Security | Session tokens shall be stored only as hashes | `auth_sessions.token_hash` (SHA-256), unique index | Implemented |
| NFR-SEC-03 | Security | All mutating and control-plane endpoints shall reject under-privileged callers | `require_role`; `tests/api/test_authorization.py` | Implemented |
| NFR-SEC-04 | Security | Every route shall have a declared exposure policy | `tests/api/test_authorization_perimeter.py` (fails on an unclassified route) | Implemented |
| NFR-SEC-05 | Security | WebSocket channels shall reject unauthenticated upgrades | close code 4401; `tests/api/test_websockets.py` | Implemented |
| NFR-SEC-06 | Security | The system shall not ship with hardcoded credentials | `.env.example` ships `change_me` placeholders; CI uses a throwaway password | Implemented |
| NFR-REL-01 | Reliability | The runtime shall survive a consumer failure without aborting the fleet loop | `tests/unit/test_runtime_resilience.py`; tick-failure guard with `MAX_CONSECISTENT_TICK_FAILURES` | Implemented |
| NFR-REL-02 | Reliability | Active trips shall never exceed the vehicle count | `tests/integration/test_active_trip_invariant.py` | Implemented |
| NFR-REL-03 | Reliability | Concurrent alert persistence shall not interleave into corrupt state | `tests/integration/test_alert_concurrency.py`; alert write lock | Implemented |
| NFR-REL-04 | Reliability | Shutdown shall complete without traceback, cancellation cascade or unretrieved task exceptions | M5.3 real console-interrupt shutdown: complete sequence in ~0.4 s, zero tracebacks; `tests/integration/test_runtime_shutdown.py` | Implemented |
| NFR-REL-05 | Reliability | A restart shall not create duplicate active runners | M5.3 acceptance (0 duplicates after restart); stale-trip recovery | Implemented |
| NFR-PERF-01 | Performance | Telemetry generation shall keep pace with the configured tick rate | 1× → ~1.1 samples/s (matches `tick_seconds = 1.0`) | Measured |
| NFR-PERF-02 | Performance | `simulation_speed` shall accelerate simulated time | 10× → 9.62 samples/s vs 1× → 1.12 samples/s (8.6×) on the M5.3 host | Measured |
| NFR-PERF-03 | Performance | Shutdown shall complete within a bounded time | ~0.4 s measured; 180 s harness ceiling | Measured |
| NFR-PERF-04 | Performance | API response latency target | No latency target was ever defined; no benchmark suite exists | **NOT QUANTIFIED** |
| NFR-PERF-05 | Performance | Concurrent-user capacity | No load test performed | **NOT QUANTIFIED** |
| NFR-REP-01 | Reproducibility | A seeded scenario shall reproduce the same telemetry across runs | M5.3 acceptance: identical sample sequences for seed 777 across two runs; a different seed differed | Measured |
| NFR-REP-02 | Reproducibility | The schema shall be reproducible from an empty database | Fresh-database migration: exit 0, single head `b7d1f3a9c2e5`, 19 tables, 8/8 checks | Measured |
| NFR-REP-03 | Reproducibility | Migrations shall render offline | `alembic upgrade head --sql` produced 365 lines of SQL without a database | Measured |
| NFR-MAI-01 | Maintainability | Analytics logic shall be unit-testable without a database | 15 unit test files covering analytics, scoring, snapshots, scenarios | Implemented |
| NFR-MAI-02 | Maintainability | Presentation rules shall be separated from interpretation | The fleet runtime produces raw measurements only; interpretation lives in `backend/analytics/*` | Implemented |
| NFR-MAI-03 | Maintainability | Automated gates shall run on every push and pull request to `develop` | `.github/workflows/ci.yml` (backend pytest + alembic; frontend test + lint) | Implemented |
| NFR-USA-01 | Usability | The dashboard shall stay consistent during live updates | WebSocket merge with REST hydration; 23 frontend suites | Implemented |
| NFR-USA-02 | Usability | Accessibility or usability metrics | No user study, no accessibility audit performed | **NOT QUANTIFIED** |
| NFR-COM-01 | Compatibility | The backend shall run on Python 3.13 with the pinned dependency set | CI `python-version: "3.13"`; local venv 3.13; `requirements.txt` fully pinned | Tested |
| NFR-COM-02 | Compatibility | The frontend shall build with Node 22 | CI `node-version: "22"`; `npm ci` + build | Tested |
| NFR-COM-03 | Compatibility | PostgreSQL 16 is the reference server | compose and CI both pin `postgres:16` | Tested in CI; the M5.3 development host ran **18.4** |
| NFR-DAT-01 | Data integrity | Unique business identifiers shall be enforced in the database | unique indexes: `ix_vehicles_vin`, `ix_vehicles_registration_number`, `ix_drivers_license_number`, `ix_users_email`, `ix_auth_sessions_token_hash`, `uq_assignments_driver_vehicle_route` | Implemented |
| NFR-DAT-02 | Data integrity | Referential integrity shall be enforced | 23 foreign keys across 18 tables | Implemented |

---

## 13. Use Case Inventory

### UC-01 — Authenticate
| Field | Value |
|---|---|
| **Primary actor** | Anonymous visitor |
| **Goal** | Obtain a session token to reach protected functionality |
| **Preconditions** | The user has an account |
| **Main flow** | 1. Submit email + password to `POST /auth/login`. 2. Server verifies the scrypt hash. 3. Server issues an opaque token, storing only its hash with an expiry. 4. Client stores it (`frontend/src/auth/tokenStorage.js`). 5. Client sends `Authorization: Bearer` thereafter. |
| **Alternative flows** | Signup creates account and session in one call; an expired/revoked token returns the client to `/login`. |
| **Exception flows** | Wrong credentials → 401; inactive user → 401; malformed body → 422 |
| **Postconditions** | An active `auth_sessions` row exists; the client holds a token |
| **Related FRs** | FR-AUTH-01…06 |
| **Evidence** | `backend/api/v1/routers/auth.py`, `tests/api/test_auth.py`, `frontend/src/pages/login.jsx` |

### UC-02 — Log out
| Field | Value |
|---|---|
| **Primary actor** | Any authenticated user |
| **Goal** | End the session |
| **Preconditions** | An active session |
| **Main flow** | 1. `POST /auth/logout`. 2. Server sets `auth_sessions.revoked_at`. 3. Client clears the token and routes to `/login`. |
| **Alternative flows** | — |
| **Exception flows** | Already-revoked/absent token → 401 |
| **Postconditions** | The token is invalid for new requests and new WebSocket connections. Open sockets are **not** terminated (C-S5). |
| **Related FRs** | FR-AUTH-04, FR-RBAC-06 |
| **Evidence** | `auth_service.py::logout`, `tests/api/test_auth.py` |

### UC-03 — Manage fleet fixtures (drivers / vehicles / routes / assignments)
| Field | Value |
|---|---|
| **Primary actor** | Administrator |
| **Goal** | Create, modify or delete the entities the simulation draws on |
| **Preconditions** | Admin session |
| **Main flow** | 1. Admin opens the Digital Twin Lab. 2. Selects an entity type. 3. Submits a form. 4. `digital_twin.py` validates references and persists. 5. UI refreshes. |
| **Alternative flows** | Reset returns the control plane to the default fixture fleet. |
| **Exception flows** | Non-admin → 403; duplicate unique value → 409 (M5.3); unknown referenced id → 404 |
| **Postconditions** | The persisted fixture set changes; the runtime uses it on the next launch |
| **Related FRs** | FR-DRV-01/02, FR-VEH-01/02, FR-ROUTE-01, FR-ASSIGN-01/02 |
| **Evidence** | `frontend/src/pages/DigitalTwinLab.jsx`, `backend/api/v1/routers/digital_twin.py`, `tests/api/test_digital_twin.py` (24 tests) |

### UC-06 — Monitor the live dashboard
| Field | Value |
|---|---|
| **Primary actor** | Viewer / Operator / Administrator |
| **Goal** | Observe live fleet state |
| **Preconditions** | Authenticated session; backend running |
| **Main flow** | 1. Open `/ws/dashboard?token=…`. 2. Server broadcasts a fleet snapshot per tick. 3. `LiveDataContext` merges snapshots with REST data. 4. Dashboard renders vehicles, health and alert counts. |
| **Alternative flows** | REST-only hydration when the socket is unavailable; client reconnects with exponential backoff. |
| **Exception flows** | Missing/invalid token → close 4401; stale connection detected client-side |
| **Postconditions** | The live view reflects the current run |
| **Related FRs** | FR-WS-01, FR-UI-01 |
| **Evidence** | `backend/api/websocket/dashboard.py`, `frontend/src/context/LiveDataContext.jsx`, `frontend/src/pages/Dashboard.jsx` |

### UC-07 — Review driver performance
| Field | Value |
|---|---|
| **Primary actor** | Viewer / Operator / Administrator |
| **Goal** | Assess a driver's behaviour and safety standing |
| **Main flow** | 1. Open Drivers. 2. Select a driver. 3. System reads `driver_statistics` (written at trip completion) plus REST analytics. 4. Drawer shows scores, grade, behaviour breakdown, trip history. |
| **Alternative flows** | Trend views via `/api/v1/analytics/drivers/{id}/trend`. |
| **Exception flows** | Unknown driver → 404 |
| **Postconditions** | None (read-only) |
| **Related FRs** | FR-ANL-03, FR-ANL-04, FR-ANL-08 |
| **Evidence** | `backend/api/v1/routers/drivers.py`, `frontend/src/pages/Drivers.jsx`, `frontend/src/components/drivers/DriverProfileDrawer.jsx` |

### UC-08 — Review vehicle health and maintenance
| Field | Value |
|---|---|
| **Primary actor** | Viewer (read) / Operator (complete) / Administrator |
| **Goal** | Assess subsystem condition and outstanding maintenance |
| **Main flow** | 1. Vehicle Health shows per-subsystem scores and reasons. 2. Maintenance lists recommendations with priority, due odometer and status. 3. An operator completes a record (`PATCH …/complete`). |
| **Alternative flows** | Thresholds via `GET /api/v1/vehicle-health/config`. |
| **Exception flows** | Non-operator completing a record → 403 |
| **Postconditions** | Maintenance status updated and persisted |
| **Related FRs** | FR-ANL-05, FR-ANL-07, FR-RBAC-03 |
| **Evidence** | `backend/analytics/vehicle_health/`, `backend/maintenance/`, `frontend/src/pages/VehicleHealth.jsx`, `Maintenance.jsx` |

### UC-09 — Triage alerts
| Field | Value |
|---|---|
| **Primary actor** | Viewer (read) / Operator (acknowledge, resolve) |
| **Goal** | Act on raised alerts |
| **Main flow** | 1. Alerts page hydrates over REST. 2. Live events arrive on `/ws/alerts`. 3. An operator acknowledges or resolves; the change persists and re-broadcasts. |
| **Alternative flows** | Auto-resolution when the underlying condition clears. |
| **Exception flows** | Duplicate suppression blocks re-emission inside the cooldown; unknown alert → 404; viewer mutation → 403 |
| **Postconditions** | Alert status/acknowledgement persisted in `alerts` |
| **Related FRs** | FR-ALT-01…04, FR-WS-03 |
| **Evidence** | `backend/alerts/`, `backend/api/v1/routers/alerts.py`, `frontend/src/pages/Alerts.jsx` |

### UC-10 — Review trip history
| Field | Value |
|---|---|
| **Primary actor** | Viewer / Operator / Administrator |
| **Goal** | Inspect completed and active trips |
| **Main flow** | 1. Trips page hydrates over REST. 2. Active trips update live via `/ws/trips`. 3. Selecting a trip opens a drawer with its snapshot and behaviour events. |
| **Alternative flows** | An operator deletes a trip or purges aborted trips. |
| **Exception flows** | Non-operator delete → 403 |
| **Postconditions** | None (read-only) unless deleted |
| **Related FRs** | FR-WS-02, FR-RBAC-03 |
| **Evidence** | `backend/api/v1/routers/trips.py`, `backend/trips/services/`, `frontend/src/pages/Trips.jsx` |

### UC-11 — View and update system settings
| Field | Value |
|---|---|
| **Primary actor** | Administrator |
| **Goal** | Inspect and change analytics configuration |
| **Preconditions** | Admin session |
| **Main flow** | 1. Open Settings. 2. `GET /settings` returns account, system and analytics configuration. 3. Admin edits a category. 4. `PATCH /settings/{category}` validates and persists as JSON with `updated_by`. |

---

## 14. Database Model

Verified against the live database (18 domain tables + `alembic_version`) and the ORM models in `backend/db/models/`. Migration head: **`b7d1f3a9c2e5`** (single head; exactly one `alembic_version` row).

| Entity (table) | Purpose | Primary key | Important attributes | Foreign keys | Key constraints |
|---|---|---|---|---|---|
| `users` | Application identities | `user_id` | `email`, `password_hash`, `full_name`, `role` (**PostgreSQL enum `user_role`**), `is_active` | — | UNIQUE `ix_users_email`; role default `operator` |
| `auth_sessions` | Bearer sessions | `session_id` | `token_hash` (SHA-256), `expires_at`, `last_used_at`, `revoked_at`, `ip_address`, `user_agent` | `user_id` → users | UNIQUE `ix_auth_sessions_token_hash` |
| `drivers` | Driver fixtures/identities | `driver_id` | `first_name`, `last_name`, `license_number`, `employment_status`, `behavior_profile` | — | UNIQUE `ix_drivers_license_number` |
| `vehicles` | Vehicles with simulation parameters | `vehicle_id` | `registration_number`, `vin`, `manufacturer`, `model`, `year`, `fuel_type`, `status`, `display_name`, `fuel_efficiency_factor`, `acceleration_response`, `tank_capacity_liters` | — | UNIQUE `ix_vehicles_vin`, UNIQUE `ix_vehicles_registration_number` |
| `routes` | Route fixtures | `route_id` | `name`, `origin`, `destination`, `route_type`, `estimated_distance_km`, `speed_limit_kmh`, `is_active` | — | — |
| `assignments` | Binds driver + vehicle + route | `assignment_id` | `name`, `notes`, `is_active` | `driver_id`, `vehicle_id`, `route_id` | UNIQUE `uq_assignments_driver_vehicle_route` |
| `trips` | One journey | `trip_id` | `start_time`, `end_time`, `distance_km`, `duration_seconds`, `fuel_used_liters`, `average_speed_kmh`, `maximum_speed_kmh`, `trip_score`, `status` | `vehicle_id`, `driver_id`, `route_id` | indexes on `vehicle_id`, `driver_id` |
| `telemetry_samples` | One generated observation | `sample_id` | `timestamp`, `speed_kmh`, `rpm`, `engine_load_percent`, `throttle_percent`, `brake_percent`, `fuel_rate_lph`, `fuel_level_percent`, `coolant_temperature_c`, `odometer_km` | `trip_id`, `vehicle_id` | indexes on `timestamp`, `trip_id`, `vehicle_id` |
| `behaviour_events` | Detected driving events | `behaviour_event_id` | event type, severity, timestamps, evidence | `vehicle_id`, `driver_id`, `trip_id` | indexes on `trip_id`, `vehicle_id` |
| `alerts` | Alert records (vehicle-scoped id) | `alert_id` | `alert_type`, `severity`, `status`, `acknowledged`, `acknowledged_at`, `last_triggered_at`, `resolved_at`, `condition`, `category`, `message`, `evidence` (JSON), `source` | `vehicle_id`, `driver_id`, `trip_id` | indexes on `severity`, `status`, `category`, `condition`, `vehicle_id` |
| `maintenance_records` | Maintenance recommendations | `maintenance_record_id` | component, priority, status, due odometer/date, estimated cost | `vehicle_id` | indexes on `status`, `vehicle_id`, `vehicle_type` |
| `vehicle_health` | Latest per-subsystem health | `vehicle_id` (also FK) | `overall_health_score`, `engine_health`, `brake_health`, `transmission_health`, `cooling_health`, `fuel_system_health`, `health_reasons` (JSON), `last_updated` | `vehicle_id` → vehicles | **1:1**; scores nullable, **no server default** (migration `b7d1f3a9c2e5`) |
| `driver_statistics` | Lifetime driver aggregates | `driver_id` (also FK) | `total_trips`, `total_distance_km`, `total_driving_time_seconds`, `average_trip_score`, `fuel_efficiency`, event counters, `safety_score`, `aggression_score`, `efficiency_score`, `last_updated` | `driver_id` → drivers | **1:1** |
| `vehicle_statistics` | Vehicle lifetime aggregates | `vehicle_id` (also FK) | `trip_count`, `total_distance_km`, `total_runtime_seconds`, `fuel_consumed_liters`, `average_fuel_efficiency`, `lifetime_health_score`, `utilization_percent`, `last_updated` | `vehicle_id` → vehicles | **1:1**; **unused by the application** (0 rows) |
| `simulation_scenarios` | Configurable simulation definition | `scenario_id` | `name`, `description`, `status`, `duration_seconds`, `simulation_speed`, `seed` | — | status default `draft` |
| `scenario_assignments` | Scenario ↔ assignment association | composite | — | `scenario_id`, `assignment_id` | association table |
| `simulation_runs` | One execution of a scenario | `run_id` | `status`, `seed`, `start_time`, `end_time`, `vehicles_active`, `trips_completed`, `error` | `scenario_id` → simulation_scenarios | index on `scenario_id` |
| `system_settings` | Configuration by category | `category` | `settings_data` (JSON), `updated_by` | `updated_by` → users | JSON default `'{}'` |

### 14.1 Live data profile (development database, M5.3)

| Metric | Value |
|---|---|
| Tables | 19 (18 domain + `alembic_version`) |

---

## 15. Relationship Model

| Relationship | Cardinality | Implementation |
|---|---|---|
| Driver → Assignment | 1:N | `assignments.driver_id` FK |
| Vehicle → Assignment | 1:N | `assignments.vehicle_id` FK |
| Route → Assignment | 1:N | `assignments.route_id` FK |
| Assignment ↔ Scenario | **M:N** | `scenario_assignments` association table |
| Scenario → Simulation Run | 1:N | `simulation_runs.scenario_id` FK |
| Vehicle → Trip | 1:N | `trips.vehicle_id` FK |
| Driver → Trip | 1:N | `trips.driver_id` FK |
| Route → Trip | 1:N | `trips.route_id` FK |
| Trip → Telemetry Sample | 1:N | `telemetry_samples.trip_id` FK |
| Vehicle → Telemetry Sample | 1:N | `telemetry_samples.vehicle_id` FK |
| Trip → Behaviour Event | 1:N | `behaviour_events.trip_id` FK |
| Vehicle / Driver → Behaviour Event | 1:N | `behaviour_events.vehicle_id`, `.driver_id` FKs |
| Trip → Alert | 1:N (nullable) | `alerts.trip_id` FK |
| Vehicle → Alert | 1:N | `alerts.vehicle_id` FK |
| Driver → Alert | 1:N (nullable) | `alerts.driver_id` FK |
| Vehicle → Maintenance Record | 1:N | `maintenance_records.vehicle_id` FK |
| Vehicle ↔ Vehicle Health | **1:1** | `vehicle_health.vehicle_id` is both PK and FK |
| Vehicle ↔ Vehicle Statistics | **1:1** | `vehicle_statistics.vehicle_id` is both PK and FK (unused) |
| Driver ↔ Driver Statistics | **1:1** | `driver_statistics.driver_id` is both PK and FK |
| User → Auth Session | 1:N | `auth_sessions.user_id` FK |
| User → System Settings (update) | 1:N | `system_settings.updated_by` FK (nullable) |
| Simulation Run → Trip / Telemetry | **indirect only** | see note below |

**ERD note — do not draw this edge:** `trips` has **no** foreign key to
`simulation_runs`. A run and the trips it produced are related only through time
and scenario configuration, not through a persisted key.

**Class-diagram note:** the ORM declares bidirectional `relationship()` attributes
for the principal aggregates (`Trip.telemetry_samples`, `Trip.behaviour_events`,
`Trip.alerts`, `Vehicle.alerts`, `Vehicle.maintenance_records`,
`Assignment.scenarios`), while the statistics companions are one-to-one with
their parent via a shared primary key.

### 16.1 Components, responsibilities and state ownership

| Component | File(s) | Responsibility | Owns state |
|---|---|---|---|
| `DriveVitalsRuntime` | `backend/application/runtime.py` | Composition root; owns the tick loop, wires analytics consumers, handles trip completion, publishes snapshots | The in-memory fleet, analytics engine, controllers |
| `SimulationController` | `backend/application/simulation_controller.py` | Start/stop/reset the run task; expose controller status | The single run task and run metadata |
| `FleetRunner` | `backend/fleet/runtime/fleet_runner.py` | Hold `VehicleRunner`s, advance all of them, report the active set | Active runners |
| `VehicleRunner` | `backend/fleet/runtime/vehicle_runner.py` | Drive one vehicle's OBD generator tick by tick; maintain trip lifecycle | One vehicle's simulation state |
| `OBDGenerator` | `backend/telemetry/generators/obd_generator.py` | Produce one telemetry sample per step from vehicle parameters | Its own seeded RNG |
| `TelemetryPipeline` | `backend/pipeline/telemetry_pipeline.py` | Fan-out of samples to registered consumers | Subscriber list |
| `AnalyticsEngine` | `backend/analytics/engine/analytics_engine.py` | Consume samples; detect and track behaviour; emit snapshots and events | Behaviour state, accumulators |
| `VehicleHealthEngine` | `backend/analytics/vehicle_health/vehicle_health_engine.py` | Score five subsystems per tick and record reasons | Health snapshots |
| `DriverStatisticsEngine` | `backend/analytics/driver_statistics/driver_statistics_engine.py` | Aggregate per-trip driver metrics and compute scores | Driver aggregates |
| `MaintenanceService` | `backend/maintenance/maintenance_service.py` | Produce component recommendations at trip completion | — |
| `AlertEngine` | `backend/alerts/alert_engine.py` + `generators/` | Derive alerts from telemetry, trips, health and maintenance | Alert cooldown state |
| `PersistenceService` | `backend/db/persistence_service.py` | All database writes; tracked background tasks; alert event emission | Background task registry |
| `DashboardBuilder` | `backend/dashboard/services/dashboard_builder.py` | Assemble the dashboard payload from trips, health and live state | Derived view state |
| `WebSocketManager` | `backend/api/websocket/manager.py` | Connection registry and fan-out broadcast | Connection set |
| `TripBuilder` / `ActiveTripBuilder` | `backend/trips/services/` | Build completed and active trip snapshots | — |

### 16.2 Communication mechanisms

| Path | Mechanism |
|---|---|
| Browser → API | HTTP JSON, `Authorization: Bearer` |
| Browser ← live state | Three WebSocket channels, each with its own `asyncio.Queue` + worker + shared manager |
| Runtime → analytics | In-process publish/consume (`TelemetryPipeline`) |
| Runtime → persistence | `asyncio` tasks tracked by `PersistenceService.schedule_background` |

---

## 16. Architecture

Verified module boundaries (237 Python files, 16 repositories, 14 routers).

```
Presentation Layer      frontend/src  (React 18 + Vite + React Router + Recharts)
   |  REST (fetch) + WebSocket (?token=)
   v
API / Realtime Layer    backend/api/
   |   FastAPI app + lifespan   backend/api/main.py
   |   14 routers               backend/api/v1/routers/
   |   security + dependencies  backend/api/security.py, backend/api/v1/dependencies.py
   |   3 WebSocket channels     backend/api/websocket/
   |   request-scoped services  backend/api/v1/services/
   v
Application Layer       backend/application/
   |   DriveVitalsRuntime    runtime.py            <- composition root + tick loop
   |   SimulationController  simulation_controller.py
   v
Domain / Analytics      backend/fleet/  backend/telemetry/  backend/analytics/
   |   FleetRunner, VehicleRunner, OBDGenerator
   |   behaviour/, vehicle_health/, driver_statistics/
   |   backend/maintenance/  backend/alerts/  backend/trips/  backend/dashboard/
   v
Persistence Layer       backend/db/  (SQLAlchemy 2.0 async + Alembic)
   |   16 ORM models, 16 repositories, 16 migrations
   v
Database                PostgreSQL (reference 16; M5.3 host ran 18.4)
```

| Foreign keys | 23 |
| Unique constraints / unique indexes | 6 |
| Enum types | 1 — `user_role` (admin, operator, viewer) |
| `vehicle_health` score server defaults | **none** (verified) |
| Rows at extraction | telemetry_samples 98,457 · behaviour_events 32,885 · trips 462 · alerts 305 · simulation_runs 54 · simulation_scenarios 37 · **vehicle_statistics 0** |

| **Alternative flows** | `GET /settings/{category}` for one category (`analytics` is the only valid category). |
| **Exception flows** | Non-admin → 403; unknown category → 404; validation failure → 422 with per-field errors |
| **Postconditions** | `system_settings.settings_data` updated |
| **Related FRs** | FR-SET-01…03, FR-RBAC-04 |
| **Evidence** | `backend/api/v1/routers/settings.py`, `backend/api/v1/services/settings_service.py`, `frontend/src/pages/Settings.jsx`, `tests/api/test_settings_integration.py` |

### UC-12 — View live telemetry
| Field | Value |
|---|---|
| **Primary actor** | Any reader, including anonymous |
| **Goal** | Inspect raw generated samples |
| **Main flow** | 1. Call `GET /api/v1/telemetry`, optionally filtered by vehicle or trip, or `latest=true`. 2. Samples render in the vehicle drawer. |
| **Alternative flows** | Live values instead come from the dashboard WebSocket snapshot. |
| **Exception flows** | `limit` outside 1..500 → 400 |
| **Postconditions** | None (read-only) |
| **Related FRs** | FR-TEL-03 |
| **Evidence** | `backend/api/v1/routers/telemetry.py`, `frontend/src/services/api/telemetryApi.js` |


### UC-04 — Configure and launch a scenario
| Field | Value |
|---|---|
| **Primary actor** | Administrator |
| **Goal** | Run a controlled, reproducible fleet simulation |
| **Preconditions** | Admin session; at least one assignment |
| **Main flow** | 1. Create a scenario with name, seed, speed, duration and assignment set. 2. `activate` marks it ready. 3. `launch` returns a `run_id`, builds the fleet from persisted assignments and starts the run task. 4. `GET /digital-twin/status` reports `running=true`. |
| **Alternative flows** | `PATCH` speed while idle; replace the assignment set via `POST /scenarios/{id}/assignments`. |
| **Exception flows** | Launch while a run is active → 409; edit a running scenario → 409; non-admin → 403; controller unavailable → 503 |
| **Postconditions** | A `simulation_runs` row with status `running`; telemetry flows |
| **Related FRs** | FR-SCN-01…03, FR-SIM-01, FR-SIM-06 |
| **Evidence** | `backend/application/simulation_controller.py`, `tests/integration/test_simulation_controller.py` |

### UC-05 — Stop a run, or let its duration expire
| Field | Value |
|---|---|
| **Primary actor** | Administrator (manual stop); System (duration expiry) |
| **Goal** | End the run and persist its outcome |
| **Preconditions** | A run is active |
| **Main flow (manual)** | 1. Admin calls `stop`. 2. Controller signals the run and awaits the task. 3. Runtime leaves the loop and writes a terminal status plus `end_time`. |
| **Main flow (duration)** | The loop compares simulated time to the deadline before each tick and breaks without a request. |
| **Exception flows** | Stop with no active run → 404 |
| **Postconditions** | `simulation_runs.status` = `completed` (natural) or `stopped` (manual); in-progress trips remain for the next launch or startup recovery |
| **Related FRs** | FR-SIM-02, FR-SIM-03, FR-SIM-07 |
| **Evidence** | `simulation_controller.py::stop`, `runtime.py` duration branch, `tests/integration/test_simulation_controller.py` |

| NFR-DAT-03 | Data integrity | A uniqueness violation shall surface as 409 and leave the session usable | `_translates_conflicts`; 3 regression tests | Implemented (M5.3) |
| NFR-DAT-04 | Data integrity | An unknown health value shall never be stored as a perfect score | migration `b7d1f3a9c2e5`; `vehicle_health` score columns nullable with no server default | Implemented |
| NFR-DAT-05 | Data integrity | A conflicting write shall be rolled back, leaving the request session usable | rollback before raising 409; `test_duplicate_conflict_leaves_the_session_usable` | Implemented (M5.3) |

| FR-WS-02 | The system shall push trip snapshots and completion events on `/ws/trips` | Authenticated | `trips.py`, `trip_publisher.py` | `test_websockets.py`, `test_trip_snapshot_contract.py` | Implemented |
| FR-WS-03 | The system shall push alert lifecycle events on `/ws/alerts` | Authenticated | `alerts.py` | `tests/api/test_websockets.py` | Implemented |
| FR-WS-04 | The system shall expose three WebSocket channels | Authenticated | `backend/api/main.py` mounts 3 WS routers | `tests/api/test_websockets.py` | Implemented |
| FR-SET-01 | An administrator shall read system settings grouped by category | Admin | `settings.py:40` | `tests/api/test_settings.py` | Implemented |
| FR-SET-02 | An administrator shall update analytics settings with validation, persisting the result | Admin | `settings.py:83`, `SettingsService.update_category` | `tests/api/test_settings_integration.py` | Implemented |
| FR-SET-03 | Settings shall persist as JSON keyed by category with the updating user recorded | Admin | `system_settings` table (`updated_by` FK) | `tests/api/test_settings_integration.py` | Implemented |
| FR-UI-01 | The dashboard shall hydrate over REST then update live over WebSocket | Authenticated | `frontend/src/context/LiveDataContext.jsx` | frontend suites | Implemented |
| FR-UI-02 | Frontend application source shall contain no mock or fixture data | Maintainers | zero matches for mock/dummy in `frontend/src` (non-test) | — | Implemented |
| FR-LIF-01 | The backend shall shut down cleanly, awaiting simulation, persistence tasks and database disposal | Operator | `main.py` lifespan; `PersistenceService.cancel_and_wait_background_tasks` | `tests/api/test_lifespan_shutdown.py`, `tests/integration/test_runtime_shutdown.py` | Implemented |

| FR-SIM-07 | Trips left `in_progress` by a previous process shall be aborted at startup | Admin | `PersistenceService.abort_stale_trips` | `test_stale_trip_abort_persistence.py` | Implemented |
| FR-SIM-08 | The control plane shall be resettable to the default fixture fleet | Admin | `digital_twin.py` reset route | `tests/api/test_digital_twin.py` | Implemented |

| FR-RBAC-02 | A viewer shall be denied every mutating endpoint with 403 | Viewer | router guards in `backend/api/v1/routers/*.py` | `tests/api/test_authorization.py` | Implemented |
| FR-RBAC-03 | An operator shall acknowledge/resolve alerts, complete maintenance, and delete trips | Operator | `alerts.py:247,269`; `maintenance.py:156`; `trips.py:104,124` | `tests/api/test_authorization.py` | Implemented |
| FR-RBAC-04 | Settings and the Digital Twin control plane shall be admin-only | Admin | `settings.py`, `digital_twin.py` (28 routes) | `tests/api/test_authorization.py` | Implemented |
| FR-RBAC-05 | Every route shall be classified public / anonymous-read / session-required / admin-only, and an unclassified new route shall fail the suite | Maintainers | `tests/api/test_authorization_perimeter.py` | itself | Implemented |
| FR-RBAC-06 | Unauthenticated WebSocket upgrades shall be closed with code 4401 | Anonymous | `backend/api/websocket/security.py` | `tests/api/test_websockets.py` | Implemented |
| FR-RBAC-07 | All three WebSocket channels shall require a valid session token | All | `dashboard.py`, `trips.py`, `alerts.py` | `tests/api/test_websockets.py` | Implemented |

| C-S3 | SYSTEM | Every WebSocket client receives every broadcast; no per-client filtering or subscription protocol | `backend/api/websocket/manager.py` |
| C-S4 | SYSTEM | WebSockets are server-push only; inbound frames are read solely to detect disconnects | `backend/api/websocket/{dashboard,trips,alerts}.py` |
| C-S5 | SYSTEM | WS session check runs once at connect; revoking a session does not close already-open sockets | `backend/api/websocket/security.py::authenticate_ws` |
| C-S6 | SYSTEM | Telemetry timestamps are simulated time, so consecutive runs of one vehicle are not strictly wall-clock ordered | `backend/application/runtime.py` advances a clock from run start |
| C-D1 | DEVELOPMENT | Docker daemon unavailable on the M5.3 host → containerized stack NOT VERIFIED | M5.3 release gate |
| C-D2 | DEVELOPMENT | `uvicorn --reload` on Windows emits asyncpg/CancelledError shutdown noise; the supported lifecycle without `--reload` is clean | `docs/LIMITATIONS.md` §Design Constraints |
| C-V1 | VERIFICATION | Docker/Compose runtime behaviour unverified (no daemon) | M5.3 gate |
| C-V2 | VERIFICATION | Performance figures come from one development host; no benchmark suite exists | §26 |
| C-V3 | VERIFICATION | No coverage measurement tooling configured (no pytest-cov) | `requirements.txt`; `docs/LIMITATIONS.md` |

| Report / export generation | No report page and no CSV/PDF export in frontend routes or API |
| External identity providers (OAuth/OIDC/SSO) | Only first-party bearer sessions exist |
| GPS / geofencing / routing engine | Routes are static fixtures (`backend/fleet/config/fleet_config.py`) |
| Driver fatigue / distraction detection | Absent from behaviour detection and alert generators |

| Aspect | Evidence-backed content |
|---|---|
| **Problem** | Fleet operators lack a repeatable, instrumented way to observe driver behaviour, vehicle condition and operational risk as trips unfold, without waiting for real vehicle hardware or workshop data. |
| **Solution** | A simulated fleet whose telemetry is produced continuously and deterministically, so the analytics, alerting and presentation pipeline can be exercised and validated end-to-end in a controlled environment. |
| **Motivation** | Educational/portfolio: demonstrate a complete telemetry-to-decision pipeline. `README.md` §"Current Scope & Limitations" states "Project demo only … not intended for production use". |
| **Future possibilities** | Physical OBD-II/CAN ingestion, ML-based scoring, predictive maintenance, anomaly detection over rolling windows, reports/export, cloud deployment (`README.md` §Future Direction). |

## 17. Digital Twin Architecture

**What the Digital Twin is here.** DriveVitals' "Digital Twin" is a **controlled
synthetic vehicle simulation environment**: a persisted, admin-configurable model
of a fleet (drivers, vehicles, routes, assignments, scenarios) plus a deterministic
physics-style generator producing OBD-II-shaped observations from it. It is
**not** a physically accurate vehicle twin and no such claim may be made.

### 17.1 Verified execution chain

```
Scenario (simulation_scenarios + scenario_assignments)
  -> SimulationController.launch()        run_id created, run task spawned
  -> DriveVitalsRuntime.configure_fleet() fleet built from persisted assignments
  -> FleetRunner.start_all()              one VehicleRunner per assignment
  -> loop: FleetRunner.tick_all(now)      once per tick
  -> VehicleRunner.tick() -> OBDGenerator.step()
  -> TelemetrySample(s)
  -> TelemetryPipeline.publish()
       -> AnalyticsEngine.consume()       behaviour detection + events
       -> VehicleHealthEngine             five subsystem scores
       -> PersistenceService              telemetry + health rows
       -> DashboardBuilder -> snapshot     -> /ws/dashboard
  -> trip completion: driver statistics, maintenance, alerts, trip update
```

### 17.2 Scenario configuration semantics

| Parameter | Storage | Verified behaviour |
|---|---|---|
| `seed` | `simulation_scenarios.seed`, copied to `simulation_runs.seed` | Seeds every vehicle generator. **Verified**: two runs with seed 777 produced identical telemetry sequences; seed 778 differed. |
| `simulation_speed` | `simulation_scenarios.simulation_speed` (default 1.0) | Loop sleeps `tick_seconds / speed`. **Verified**: 10× → 9.62 samples/s vs 1× → 1.12 samples/s (8.6×). |
| `duration_seconds` | `simulation_scenarios.duration_seconds` | Deadline = `start_time + duration`, checked **before** each tick so a run never overshoots. **Verified**: a 5 s scenario ended on its own; run row became `completed` with an `end_time`. |
| assignment set | `scenario_assignments` | Determines participating drivers/vehicles/routes. |

### 17.3 Simulation time

---

## 18. Telemetry Pipeline

### 18.1 One observation, end to end

1. **Generation** — `OBDGenerator.step()` produces a `TelemetrySample` from vehicle parameters, the seeded RNG and the current simulated time.
2. **Runtime object** — `VehicleRunner.tick()` records speed into the trip, updates odometer and fuel, returns the sample.
3. **Fan-out** — `TelemetryPipeline.publish()` calls every registered consumer.
4. **Analytics** — `AnalyticsEngine.consume()` updates runtime state, runs behaviour detection, tracks events and accumulators; `VehicleHealthEngine` scores the five subsystems.
5. **Persistence** — `PersistenceService.persist_telemetry()` writes one `telemetry_samples` row per sample; `brake_pressure` (0–1) is converted to `brake_percent` (0–100).
6. **Presentation** — `DashboardBuilder` folds live values into a snapshot; `DashboardSnapshotPublisher` enqueues it.
7. **Delivery** — `/ws/dashboard` broadcasts `{type: "dashboard_snapshot", data: {...}}`; REST serves `/api/v1/telemetry`.
8. **Frontend** — `LiveDataContext` merges snapshots with REST data; adapters and draw components render it.

### 18.2 Field inventory and units

| Field | Unit | Note |
|---|---|---|
| `speed_kmh` | km/h | |
| `rpm` | rev/min | derived from speed |
| `engine_load_percent` | % 0–100 | derived from throttle and RPM |
| `throttle_percent` | % 0–100 | **REST** name; the WebSocket snapshot calls it `throttle_position_percent` |
| `brake_percent` | % 0–100 | in-memory `brake_pressure` is 0.0–1.0, converted at persistence |
| `fuel_rate_lph` | L/h | |
| `fuel_level_percent` | % 0–100 | |
| `coolant_temperature_c` | °C | |
| `odometer_km` | km | cumulative per vehicle |

---

## 19. Analytics Pipeline

All analytics are **RULE-BASED** (threshold and formula evaluation). No statistical
model fitting, no learning, no inference.

### 19.1 Driver behaviour — RULE-BASED

| Property | Content |
|---|---|
| Input | One `TelemetrySample` + `RuntimeAnalyticsState` + `AnalyticsContext` (route speed limit) |
| Processing | `DriverBehaviourAnalyzer.analyze()` applies fixed thresholds |
| Thresholds | speeding: `speed_kmh > speed_limit`; harsh braking: `brake_pressure ≥ 0.75` **and** `speed_kmh ≥ 20`; aggressive throttle: `throttle_position_percent ≥ 80`; high RPM: `rpm ≥ 4000` |
| Severity | normal / minor / moderate / severe from the combination and magnitude |
| Output | `DriverBehaviourAnalysis`, tracked `BehaviourEvent`s, per-trip summary |
| Persistence | `behaviour_events` rows at trip completion |
| Frontend | Dashboard live flags, Trip drawer, Drivers page |
| Evidence | `backend/analytics/behaviour/detection/analyzer.py`, `events/tracker.py`, `aggregation/summarizer.py` |

### 19.2 Driver statistics and the canonical safety score — RULE-BASED / DERIVED METRIC

| Property | Content |
|---|---|
| Input | Completed-trip behaviour summary + trip distance |
| Processing | Weighted density `(2.0·harsh_brake + 1.5·harsh_accel + 3.0·overspeed + 1.0·high_rpm) / distance_km`; then `score = 100 · exp(−0.35 · density)`, clamped to [0, 100], rounded to 2 dp |
| Grade | A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 60, else F |
| Properties | Distance-normalised, so the same number of events penalises a short trip more than a long one; because the deduction is density-based, clean driving lets the score recover |
| Canonical owner | `backend/analytics/driver_statistics/safety.py` — the **only** implementation |
| Consumers | `runtime.py` (trip score), `trips/services/trip_builder.py`, `driver_score_calculator.py` |
| Persistence | `trips.trip_score`; `driver_statistics.safety_score` / `aggression_score` / `efficiency_score` |
| Frontend | Trips page, Drivers page, dashboard |
| Evidence | `safety.py`, `config.py` (constants), `tests/unit/test_safety_scoring.py`, `test_safety_score_sources.py` |

**Single-score confirmation:** a codebase-wide search found exactly one
`compute_safety_score` implementation and one `compute_grade`. Other
`safety_score` occurrences are reads, projections or aggregations (for example
`average_safety_score` in the trip publisher), not a second algorithm.

### 19.3 Vehicle health — RULE-BASED

| Property | Content |
|---|---|
| Input | Rolling telemetry windows per vehicle |
| Processing | Five subsystem analyzers, each scoring 0–100 with explicit thresholds and reason strings |

---

## 20. Safety Score Source of Truth

### 20.1 The single canonical path

```
TelemetrySample (per tick, per vehicle)
   |
   v  DriverBehaviourAnalyzer (fixed thresholds)
BehaviourEvent  [speeding | harsh_braking | aggressive_throttle | high_rpm]
   |
   v  EventTracker + Summarizer (coalescing, per-trip counts)
DriverBehaviourSummary {harsh_braking_count, aggressive_throttle_event_count,
                        speeding_event_count, high_rpm_event_count}
   |
   v  compute_safety_score_for_summary(summary, distance_km = TRIP distance)
trip score -> trips.trip_score -> TripSnapshot.safety_score -> REST + /ws/trips

Trip completion -> DriverStatisticsEngine -> DriverScoreCalculator
   -> driver_statistics.safety_score (lifetime) -> /driver-statistics -> Drivers page
```

### 20.2 The algorithm (as implemented, not inferred)

```
weighted_density = (2.0 * harsh_braking_count
                  + 1.5 * harsh_acceleration_count
                  + 3.0 * overspeed_count
                  + 1.0 * high_rpm_count) / distance_km

if weighted_density is infinite:  score = 0.0
else:                             score = 100.0 * exp(-0.35 * weighted_density)

score = clamp(round(score, 2), 0, 100)
grade = A if score>=90 else B if >=80 else C if >=70 else D if >=60 else F
```

Constants live in `backend/analytics/driver_statistics/config.py`:
`SAFETY_START=100.0`, `SAFETY_WEIGHT_HARD_BRAKE=2.0`,
`SAFETY_WEIGHT_HARD_ACCELERATION=1.5`, `SAFETY_WEIGHT_OVERSPEED=3.0`,
`SAFETY_WEIGHT_HIGH_RPM=1.0`, `SAFETY_DENSITY_SENSITIVITY=0.35`.

### 20.3 Single-score confirmation

- Exactly one `compute_safety_score` implementation (`safety.py:29`).
- Exactly one `compute_grade` implementation (`safety.py:88`).
- `trips.trip_score`, `driver_statistics.safety_score` and any
  `average_safety_score` in WebSocket payloads are **projections of that one

---

## 21. Alert Pipeline

```
Telemetry / health / trip aggregates / maintenance state
   |
   v  AlertEngine + generators (thresholds)      backend/alerts/
Alert candidate (type, severity, category, condition, message, evidence, source)
   |
   v  deduplication.py -- same key inside the cooldown is suppressed
   |
   v  PersistenceService.persist_alerts()  (write lock)
alerts row [vehicle-scoped alert_id, status=active, acknowledged=false]
   |
   +--> /ws/alerts  {type:"alert_event", data:{... alert_created ...}}
   +--> REST GET /api/v1/alerts -> Alerts page
   |
   v  condition clears
resolve_cleared_alerts() -> status=resolved, resolved_at set
   |
   v  operator acknowledges / resolves
POST /api/v1/alerts/{alert_id}/acknowledge | /resolve   [operator role]
   |
   +--> /ws/alerts (alert_acknowledged / alert_resolved)
```

| Aspect | Verified detail |
|---|---|
| Alert types | telemetry: `telemetry_engine_overheating`, `telemetry_coolant_critical`, `telemetry_fuel_critical`, `telemetry_rpm_redline`; trip: `trip_overspeeding`, `trip_repeated_harsh_braking`, `trip_repeated_harsh_acceleration`, `trip_aggressive_driving`, `trip_unsafe`; plus health and maintenance generators |
| Severity | `SEVERITY_RANK` ordering over normal/minor/moderate/severe, mapped from priority and health status |
| Categories | `ALERT_CATEGORY` map plus `health_category()` for health-derived alerts |
| Identity | `alert_id` is **vehicle-scoped**, so the frontend can reconcile WS events against REST rows |
| Concurrency | Alert persistence serialised by a write lock; `tests/integration/test_alert_concurrency.py` |
| Stale alerts | `resolve_stale_trip_alerts` handles alerts whose trip ended |
| Evidence | `backend/alerts/`, `backend/db/persistence_service.py`, `tests/integration/test_alert_lifecycle.py` |

| Aggregation | Weighted sum: engine 0.30, cooling 0.20, brakes 0.20, transmission 0.15, fuel system 0.15 |
| Output | `overall_health_score`, five subsystem scores, `health_reasons` JSON |
| Persistence | `vehicle_health` upsert per tick; scores nullable with **no** server default |
| Frontend | Vehicle Health page, vehicle drawer, dashboard cards |
| Evidence | `backend/analytics/vehicle_health/`, `tests/unit/test_health_reasons.py` |

### 19.4 Maintenance estimation — RULE-BASED

| Property | Content |
|---|---|
| Input | Vehicle condition at trip completion (health scores + odometer) |
| Processing | `ComponentEstimator` plus per-component estimators (engine, brakes, cooling, transmission, fuel system) against `maintenance_config.py` rules |
| Output | Recommendation: component, priority, due odometer, estimated cost, description |
| Persistence | `maintenance_records` at trip completion; duplicate reconciliation exists |
| Frontend | Maintenance page |
| Evidence | `backend/maintenance/estimators/`, `estimation/rules.py`, `tests/integration/test_intelligence_persistence.py` |

### 19.5 Alerts — RULE-BASED

| Property | Content |
|---|---|
| Input | Telemetry conditions, trip aggregates, health states, maintenance state |
| Generators | `telemetry_alerts.py` (engine overheating, coolant critical, fuel critical, RPM redline), `trip_alerts.py` (overspeeding, repeated harsh braking, repeated harsh acceleration, aggressive driving, unsafe trip), `health_alerts.py`, `maintenance_alerts.py` |
| Categories | vehicle-scoped, mapped by `ALERT_CATEGORY` / `health_category()` |
| Deduplication | `backend/alerts/deduplication.py` with a cooldown window per alert key |
| Resolution | `resolve_cleared_alerts` auto-resolves when the condition clears; an operator may resolve manually |
| Concurrency | A write lock serialises alert persistence |
| Persistence | `alerts` rows keyed by a vehicle-scoped `alert_id` |
| Frontend | Alerts page (REST hydration + `/ws/alerts` events) |
| Evidence | `backend/alerts/`, `alerts_config.py`, `tests/integration/test_alert_lifecycle.py`, `test_alert_concurrency.py` |

### 19.6 Trip and fleet analytics — AGGREGATION

| Property | Content |
|---|---|
| Input | Persisted trips, behaviour events, statistics, alerts |
| Processing | Aggregation and derivation for fleet summary, per-vehicle, per-driver, trend series, insights |
| Output | `/api/v1/analytics/{summary,vehicles,drivers,drivers/{id}/trend,trips,events,events/trend,fleet-trend,insights,safety-distribution}` |
| Evidence | `backend/api/v1/routers/analytics.py`, `tests/test_analytics_api.py` |


### 18.3 Derived metrics and their source

| Metric | Derived from | Where computed |
|---|---|---|
| Safety score | Weighted behaviour-event **density** per km | `analytics/driver_statistics/safety.py` |
| Grade A–F | Safety score thresholds | `safety.py::compute_grade` |
| Overall health | Weighted sum of 5 subsystems (engine 0.30, cooling 0.20, brakes 0.20, transmission 0.15, fuel system 0.15) | `analytics/vehicle_health/health_config.py` |
| Health reasons | Per-subsystem rule evaluation | `analytics/vehicle_health/health_reasons.py` |
| Trip metrics | Accumulated sample deltas | `runtime.py::_finalize_trip_metrics` |
| Live fuel used | Fuel-level drop × fixed 60 L (**documented gap**) | `dashboard_builder.py` |
| Persisted trip fuel | Fuel-level drop × per-vehicle `tank_capacity_liters` | `runtime.py` |


- The runtime advances a simulation clock from the run's start time; the `now` passed to each tick is that simulated time.
- Tick interval at 1× is `tick_seconds = 1.0` s; at speed *s* the sleep is `1.0 / s` s.
- **Consequence (C-S6):** `telemetry_samples.timestamp` is simulated time, so at high speed a run's samples can be timestamped ahead of wall clock, and a later slower run of the same vehicle can carry earlier timestamps. Consumers needing arrival order must key on the trip.

### 17.4 Lifecycle control

| Action | Endpoint | Behaviour |
|---|---|---|
| Activate | `POST /scenarios/{id}/activate` | Marks the scenario ready |
| Launch | `POST /scenarios/{id}/launch` | Creates a run, builds the fleet, starts the loop, returns `run_id`; a concurrent launch is refused |
| Stop | `POST /scenarios/{id}/stop` | Signals the run task, awaits it, writes terminal status |
| Duration expiry | automatic | Loop breaks at the deadline; status becomes `completed` |
| Run history | `GET /scenarios/{id}/runs` | Persisted runs with status, seed, times, counters |
| Reset | `POST /digital-twin/reset` | Restores the default fixture fleet |
| Recovery | application startup | `abort_stale_trips` clears trips left `in_progress` by a previous process |

**Verified in M5.3:** launch → live telemetry → dashboard snapshot → duration expiry → restart with zero duplicate active runners.

| Analytics → DB | `AsyncSession` via repositories (`backend/db/repositories/`) |
| Component → component | Direct method calls / callbacks (single process, no broker) |


---

## 22. WebSocket Architecture

### 22.1 Endpoints (three — verified)

| Endpoint | Payload `type` | Publisher | Worker |
|---|---|---|---|
| `/ws/dashboard` | `dashboard_snapshot` | `DashboardSnapshotPublisher` (`websocket/snapshot_publisher.py`) | `snapshot_worker` |
| `/ws/trips` | `trips_snapshot` | `TripSnapshotPublisher` (`websocket/trip_publisher.py`) | `trips_worker` |
| `/ws/alerts` | `alert_event` (inner type `alert_created` / `alert_acknowledged` / `alert_resolved`) | `PersistenceService` → `alerts_queue` | `alerts_worker` |

### 22.2 Mechanism

- One `asyncio.Queue` per channel; internal code calls `put_nowait`.
- One worker task per channel drains its queue and broadcasts.
- `WebSocketManager` (`websocket/manager.py`) holds connections and fans out to **all** of them — no per-client filtering (constraint C-S3).
- Endpoints are **server-push only**: the handler reads inbound text frames solely to detect disconnects (constraint C-S4).
- Each endpoint authenticates once with a short-lived DB session, releases it, then enters the receive loop (`backend/api/websocket/security.py`).

### 22.3 Authentication

- `?token=<session token>` query parameter (browsers cannot set WebSocket headers).
- Failure → close code **4401**, reason `Unauthenticated: missing, invalid or expired session token`.
- Revocation after connect does not close an open socket (C-S5).

### 22.4 Frontend consumer

- `frontend/src/websocket/connectionManager.js` — reconnect with exponential backoff plus jitter, heartbeat/stale-connection detection, and a fresh token read per connection attempt (commit `1a23e7f`).
- `frontend/src/context/LiveDataContext.jsx` — subscribes and merges into React state.
- The client detects staleness by absence of messages; the backend sends no heartbeats.

**Correction for the report:** older documentation described "two unauthenticated
WebSocket endpoints". The implemented system has **three authenticated** channels.

---

## 23. Frontend Architecture

### 23.1 Routes (verified in `frontend/src/App.jsx`)

| Route | Page | Protection |
|---|---|---|
| `/` | `Introductionpage.jsx` (Get Started) | public |
| `/login`, `/signup` | `login.jsx`, `signup.jsx` | public |
| `/dashboard` | `Dashboard.jsx` | `ProtectedRoute` |
| `/fleet` | `Fleet.jsx` | `ProtectedRoute` |
| `/trips` | `Trips.jsx` | `ProtectedRoute` |
| `/drivers` | `Drivers.jsx` | `ProtectedRoute` |
| `/alerts` | `Alerts.jsx` | `ProtectedRoute` |
| `/analytics` | `Analytics.jsx` | `ProtectedRoute` |
| `/vehicle-health` | `VehicleHealth.jsx` | `ProtectedRoute` |

---

## 24. Technology Stack

| Layer | Technology | Version | Purpose | Verified |
|---|---|---|---|---|
| Backend runtime | Python | 3.13 (CI + local venv) | Application language | Yes |
| Web framework | FastAPI | 0.139.0 | REST + WebSocket server | Yes |
| ASGI server | Uvicorn | 0.49.0 | Application server | Yes |
| ASGI base | Starlette | 1.3.1 | FastAPI foundation | Yes |
| ORM | SQLAlchemy (async) | 2.0.51 | Data access | Yes |
| DB driver | asyncpg | 0.31.0 | Async PostgreSQL driver | Yes |
| Migrations | Alembic | 1.18.5 | Schema versioning | Yes |
| Env config | python-dotenv | 1.2.2 | `.env` loading | Yes |
| WS client (tests/tooling) | websockets | 16.0 | WebSocket client library | Yes |
| Validation | Pydantic | via FastAPI | Request/response schemas | Yes |
| Database | PostgreSQL | 16 reference (compose + CI); 18.4 on the M5.3 host | Data store | Yes |
| Frontend | React / React DOM | ^18.2.0 | UI | Yes |
| Routing | react-router-dom | ^7.18.1 | Client routing | Yes |
| Charts | recharts | ^3.10.1 | Visualisation | Yes |
| Icons | lucide-react | ^1.27.0 | Icon set | Yes |
| Build tool | Vite | ^5.2.0 | Dev server + build | Yes |
| React plugin | @vitejs/plugin-react | ^4.2.1 | JSX transform | Yes |
| Unit testing | Vitest | ^4.1.10 | Frontend tests | Yes |
| Linting | ESLint (+ react-hooks, react-refresh) | ^10.8.0 | Static analysis | Yes |
| Backend testing | pytest / pytest-asyncio / httpx | 9.1.1 / 1.4.0 / 0.28.1 | Test stack | Yes |
| CI | GitHub Actions | — | Automated gates on `develop` | Yes |
| Containers | Docker + Docker Compose | — | Local 4-service environment | **CONFIGURED, NOT VERIFIED** |
| ML/AI | — | — | — | **Not present** |
| Message broker / cache | — | — | — | **Not present** |

---

## 25. Development Environment

| Item | Value | Status |
|---|---|---|
| OS (M5.3 verification host) | Windows 11 | TESTED |
| Python | CPython 3.13 (local venv and CI) | TESTED |
| Node.js | 22 (CI) | TESTED |
| Package managers | `pip` (pinned `requirements.txt`), `npm ci` | TESTED |
| Database | PostgreSQL 18.4 locally; 16 in compose/CI | TESTED (18.4) / CONFIGURED (16) |
| Backend URL | `http://localhost:8000` | TESTED |
| Frontend URL | `http://localhost:5173` (Vite dev server) | TESTED |
| Environment file | `.env` at repository root (git-ignored), `.env.example` as template | TESTED |
| Required env vars | `POSTGRES_PASSWORD` (mandatory); `POSTGRES_USER/HOST/PORT/DB`, `ACCESS_TOKEN_TTL_HOURS` (default 24), `CORS_ORIGINS` (default `http://localhost:5173`), `BOOTSTRAP_ADMIN_EMAIL/PASSWORD/NAME` (optional, all three together) | TESTED |
| Alembic | `backend/alembic.ini`, migrations in `backend/db/migrations/versions/` | TESTED |
| Docker | daemon unavailable on the M5.3 host | **NOT VERIFIED** |
| IDE | not recorded as a system requirement | — |

---

## 26. Testing Evidence

### 26.1 Final M5.3 results (re-verified during this extraction where possible)

| Gate | Result | Status |
|---|---|---|
| Backend suite | **525 passed** (48 test files) | Verified |
| Frontend suite | **265 passed / 23 files** | Verified |
| ESLint | clean | Verified |
| Vite production build | success, 2,593 modules, ~24 s | Verified |
| Alembic single head | `b7d1f3a9c2e5` | Verified |
| Fresh-database migration | 8/8 checks (exit 0, 19 tables, no `vehicle_health` score defaults, unique indexes present, re-upgrade is a no-op) | Verified |
| Offline SQL generation | `alembic upgrade head --sql` → 365 lines | Verified |
| End-to-end acceptance | **45/45 PASS** against a live server | Verified (see note) |
| Credential scan | clean | Verified |
| Docker runtime | daemon unavailable | **NOT VERIFIED** |

**Note on the acceptance run:** the 45-check harness was a scratch verification
tool used during M5.3. It was intentionally **not committed** (it lives outside the
tracked tree), so it is *evidence of a verification run*, not a repository artefact.
The committed regression evidence is the pytest and Vitest suites.

---

## 27. Known Limitations (current, verified)

Only limitations still true at `b8864f2`. Fixed or removed limitations are **not** listed.

### 27.1 Functional limitations

| ID | Limitation | Verification |
|---|---|---|
| L-01 | Telemetry is synthetic; no CAN/OBD-II hardware ingestion | `OBDGenerator` is the only producer |
| L-02 | No machine learning or AI anywhere in the system | no ML dependency; analytics are threshold-driven |
| L-03 | No reports or data export (no CSV/PDF) | absent from routes and API |
| L-04 | No external identity providers (OAuth/OIDC/SSO), no password reset | only first-party bearer sessions |
| L-05 | No GPS, geofencing, terrain detection or map integration | routes are static fixtures |
| L-06 | No driver fatigue or distraction detection | absent from behaviour detection |
| L-07 | No ERP / logistics integration | not present |
| L-08 | Default fixture fleet is 6 vehicles/drivers/routes/assignments | `backend/fleet/config/fleet_config.py` |
| L-09 | The live dashboard fuel estimate uses a fixed 60 L tank instead of the vehicle's configured capacity | `dashboard/services/dashboard_builder.py` |
| L-10 | Frontend adapters render `0` for an absent live signal, so "no value" can read as a real zero | `DriverProfileDrawer.jsx`, `DriverCard.jsx` |
| L-11 | The `vehicle_statistics` table is never written or read (0 rows) | live database; no repository uses it |

### 27.2 Architectural and operational limitations

| ID | Limitation |
|---|---|
| L-12 | Single-process asyncio runtime; no horizontal scaling, load balancing or caching |
| L-13 | In-memory analytics state is lost on restart and rebuilt |
| L-14 | WebSocket delivery is fan-out to all clients; no per-client filtering or subscription protocol |
| L-15 | WebSockets are server-push only; inbound frames are discarded except for disconnect detection |
| L-16 | A WebSocket session is validated only at connect time |
| L-17 | Telemetry timestamps are simulated time, not arrival time |
| L-18 | `simulation_speed` sets the tick interval, so the achieved rate lands slightly below the requested multiplier (8.6× measured for 10×) |

### 27.3 Verification and environment limitations

---

## 28. Documentation Contradiction Audit

Documentation was **not modified** during this extraction, per the task rules. Each
row states the actual implementation and the action required. **HIGH** rows directly
contradict the shipped system.

| ID | Document | Claim (with location) | Actual implementation | Severity | Required action |
|---|---|---|---|---|---|
| C-01 | `README.md:272` | "**No authentication** — the login/signup pages are static UI with no backend auth router, session handling, or user model." | Full auth is implemented: `backend/api/v1/routers/auth.py`, scrypt hashing, opaque bearer sessions, RBAC, `tests/api/test_auth.py` | **HIGH** | Delete or rewrite. Self-contradicted by `README.md:289`, which marks the same item *shipped*. |
| C-02 | `README.md:273` | "**No cloud deployment** … Docker provisions PostgreSQL only; containerized app deployment is not implemented." | `docker-compose.yml` defines four services: `postgres`, `migration`, `backend`, `frontend` | **HIGH** | Rewrite. Self-contradicted by `README.md:291`. Keep the caveat that the stack is NOT VERIFIED (L-19). |
| C-03 | `README.md:275` | "**Frontend-backend REST integration is partial** — … some REST-backed views still use mock data as a fallback." | Zero mock/dummy/placeholder matches in `frontend/src` application source; views hydrate over REST and update over WebSocket | MEDIUM | Delete; contradicted by `README.md:289`. |
| C-04 | `backend/README.md:247` | "**No authentication/authorization**: all endpoints (REST and WebSocket) are public; no RBAC or audit logging." | RBAC is enforced on every mutation and control-plane route; the fleet read surface is anonymous **by policy** and regression-tested | **HIGH** | Rewrite; replace with the actual exposure policy (§10.4). |
| C-05 | `frontend/README.md:91` (also line 61) | "`/login`, `/signup` — **Static demo UI only — no authentication exists**" | Login/signup call `/api/v1/auth/login|signup`; `AuthContext`, `tokenStorage`, `ProtectedRoute`, `RoleRoute` implement the session lifecycle | **HIGH** | Rewrite both locations. |
| C-06 | `docs/fyp/DriveVitals_Document_Generation_Report.md:92` | "No seeded/reproducible-run determinism claim (**scenario seed not wired to runtime RNG** — marker retained)" | The seed **is** wired to the runtime RNG and determinism was **verified** in M5.3: identical telemetry across two runs of seed 777; seed 778 diverged | **HIGH** | Replace the marker. The FYP may make a *seeded reproducibility* claim citing FR-SIM-04. |
| C-07 | `docs/ANALYTICS.md:201` | "Future fuel-efficiency scoring is planned but not implemented." | `DriverScoreCalculator` computes `efficiency_score`; `driver_statistics.fuel_efficiency` is persisted and exposed via `/api/v1/analytics/drivers` | MEDIUM | Rewrite. The adjacent point that fuel is not reported as a standalone km/L metric may stand, but must not deny efficiency scoring. |
| C-08 | `docs/LIMITATIONS.md` (this repository) | "`vehicle_statistics` … with a legacy `lifetime_health_score DEFAULT 100`" | True **only** for a database created by replaying the migration chain (`020b8a858c0a` sets `server_default="100.0"`). The long-lived development database has **no** server defaults on that table | LOW–MEDIUM | Reword to name the migration as the source and record the development-database divergence (§39, Q-04). |
| C-09 | `README.md` badge and technology table | "PostgreSQL 16" | compose and CI pin `postgres:16`; the M5.3 development host ran **18.4** | LOW | Keep 16 as the reference; note the tested host version if precision matters. |
| C-10 | `docs/design/frontend/dashboard_design.md`, `docs/design/backend/api_design.md`, `docs/design/backend/backend_modules.md`, `docs/DOCUMENTATION_AUDIT.md` | Design-era descriptions: two WebSocket channels, no auth router, PostgreSQL-only Docker, "no REST endpoints for telemetry or analytics" | Superseded by the implementation | LOW (historical) | Label clearly as **historical design records**; never cite as current behaviour. `docs/README.md` already states this rule. |
| C-11 | `docs/Project_Bible/*.md` | Vision/scope material including intended AI coaching and route optimisation | Partly aspirational | LOW (historical) | Treat as project-definition history, not implementation evidence. |

### 28.1 Resolved during M5.3 (for completeness)

| Former claim | Current state |
|---|---|
| "10 REST routers", "Two WebSocket channels", "unauthenticated WebSockets" | 14 routers / 74 operations; three authenticated channels |
| "35 backend test files (298 tests) / 15 frontend suites" | 48 files / 525 tests; 23 suites / 265 tests |
| "No CI workflow", "not containerized" | CI workflow exists; Compose runs four services |
| README "Reports / exportable reports" page | removed — no such page exists |
| `test_empty.py` "contains no tests" | contains three empty-database tests |


---

## 29. Chapter 1 Fact Sheet

### 29.1 Problem statement — evidence material (do not write the sentence yet)

Material from which exactly **one** sentence may later be written:

- Real fleet data requires physical vehicles, CAN/OBD-II hardware and workshop history, all of which are expensive, slow and unavailable for continuous study (§4.2).
- Driver behaviour, vehicle condition and operational risk are normally observed after the fact rather than continuously (§19).
- A controlled, repeatable environment is therefore needed in which a telemetry-to-analytics-to-decision pipeline can be exercised and validated end to end (§17).
- The implemented answer is a simulated fleet with a configurable, seeded control plane (§17.1–17.2).

### 29.2 Objectives — measurable, implementation-supported

| ID | Objective | Support |
|---|---|---|
| OBJ-01 | Provide a controlled synthetic fleet simulation with an admin-configurable control plane | §17, FR-SCN-01…03, FR-SIM-01 |
| OBJ-02 | Generate OBD-II-shaped telemetry continuously and deterministically | FR-TEL-01, FR-SIM-04, NFR-REP-01 |
| OBJ-03 | Derive driver, vehicle, trip and fleet insight through deterministic rule-based analytics | §19, FR-ANL-01…08 |
| OBJ-04 | Detect, persist and resolve alerts with de-duplication | §21, FR-ALT-01…03 |
| OBJ-05 | Persist all operational data in a relational store with a versioned schema | §14, NFR-REP-02/03 |
| OBJ-06 | Deliver live state to a browser dashboard over authenticated WebSockets | §22, FR-WS-01…04 |
| OBJ-07 | Enforce authentication and role-based authorization across API and dashboard | §10, FR-AUTH-*, FR-RBAC-* |
| OBJ-08 | Validate the system with automated unit, integration and API test suites | §26, 525 + 265 tests |

### 29.3 Research hypothesis / questions

**This project contains no research component.** It is a product-focused FYP.

- No hypothesis was formulated, tested or refuted.
- No experiment was designed to answer a research question.
- No novel method, dataset or theory was produced; the analytics are standard threshold rules (§19).

---

---

## 30. Chapter 2 Fact Sheet

**No literature review is written here.** This section fixes what must later be
compared and separates verified implementation facts from research still to be done.

### 30.1 System category (for the comparison set)

- Fleet telematics platforms and driver-behaviour-monitoring products
- Vehicle health / predictive-maintenance systems
- Digital Twin simulation environments for vehicles
- Real-time web monitoring dashboards (as an implementation pattern)
- Rule-based (non-ML) driving analytics

### 30.2 Comparison dimensions

| Dimension | DriveVitals' verified position |
|---|---|
| Fleet monitoring | Implemented: dashboard, fleet, trips, alerts views |
| Synthetic telemetry | Implemented and reproducible via seed |
| Digital Twin control | Implemented: scenario CRUD, assignment sets, launch/stop/duration |
| Driver analytics | Implemented: behaviour detection, canonical distance-normalised safety score, lifetime statistics |
| Vehicle health | Implemented: five subsystems, weighted aggregate, reasons |
| Alerting | Implemented: four generator families, deduplication, auto-resolution |
| Real-time dashboard | Implemented: three authenticated WebSocket channels |
| Scenario configuration | Implemented: seed, speed, duration, assignment selection |
| Reproducibility | Implemented and measured: identical telemetry for a fixed seed |
| Authentication / RBAC | Implemented: three roles, server-enforced |
| Physical vehicle integration | **Absent** |
| ML / AI analytics | **Absent** |
| Cloud / fleet-scale deployment | **Absent** |

### 30.3 Gap framing

The defensible combination DriveVitals actually demonstrates is:
**a reproducible, scenario-configurable synthetic fleet environment whose telemetry
feeds deterministic driver, vehicle, trip and alert analytics, persisted relationally
and streamed live to an authenticated dashboard.**

Novelty must **not** be claimed: each individual technique (threshold behaviour
detection, distance-normalised scoring, WebSocket dashboards, seeded simulation) is
established practice. The contribution is their integration in one verifiable system.

### 30.4 Implementation facts vs. literature to be researched

| IMPLEMENTATION FACTS (already verified) | LITERATURE TO BE RESEARCHED |
|---|---|
| every item in §4.1, §14–§24 | Commercial telematics platforms and their feature sets |
| every measured figure in §26 | Fleet monitoring and telematics architecture literature |
| every limitation in §27 | OBD-II / CAN protocol background (engineering reference only here) |
| the contradiction audit in §28 | Digital Twin definitions in academic literature |
| | Driver-behaviour-scoring and eco-driving metrics in the literature |
| | Predictive-maintenance and anomaly-detection methods (the future-work direction) |

**Rule:** no sentence in Chapter 2 may cite an implementation fact as prior art, and
no literature claim may be introduced without a retrievable source.

## 31. Chapter 3 Fact Sheet

| Section | Source in this DST |
|---|---|
| System environment | §16 (architecture), §25 (dev environment), §4.2 (excluded) |
| External interfaces | §10.5 (WebSocket auth), §16.2 (communication mechanisms), §22 |
| User interfaces | §23.1 (routes and protection), §23.2 |
| Hardware/software environment | §24 (technology stack), §25 |
| Assumptions | §7 (A-01…A-06) |
| Constraints | §8 (C-S*, C-D*, C-V*) |
| Functional requirements | §11 (FR-*) |
| Non-functional requirements | §12 (NFR-*) |
| Actors | §9 (table) |
| Use cases | §13 (UC-01…UC-12) |

**Writing rule for Chapter 3:** every requirement row must carry the same
`ID | requirement | actor | evidence | test | status` shape used in §11, so the
traceability matrix in §36 can be built without re-deriving anything. Requirements
that are NOT IMPLEMENTED must not appear as requirements; they belong in Chapter 1's
delimitations or in limitations.

---

## 32. Chapter 4 Fact Sheet

| Section | Prepared material |
|---|---|
| System architecture | §16 layer diagram + §16.1 component table (component, file, responsibility, owned state) |
| Component architecture | §16.1, §17.1 (execution chain), §19 (analytics components), §22 (realtime) |
| Deployment architecture | §25 + `docker-compose.yml` (postgres → migration → backend → frontend, with health conditions). **Mark as configuration, not verified runtime (L-19).** |
| ERD | §14 (18 entities) + §15 (cardinalities) + the "no Run→Trip FK" note |
| Class diagram candidates | ORM aggregates: `Vehicle`, `Driver`, `Route`, `Assignment`, `Trip`, `SimulationScenario`, `SimulationRun`, plus the 1:1 statistics companions (§14, §15 notes) |
| Sequence diagram candidates | (1) Authentication + WebSocket connect; (2) Digital Twin launch; (3) Telemetry sample → analytics → persistence → dashboard → browser |
| Activity diagram candidates | Scenario lifecycle (create → configure → activate → launch → run → duration/manual stop → history) |
| DFD 0 / 1 / 2 | Derive from §18 (telemetry flow), §21 (alert flow), §19 (analytics), §22 (delivery) |

Every proposed diagram must state: what it represents, the components involved, the
evidence source, and the likely relationships — before any diagram is drawn.

- The Draft 0.1 report already omits §1.3 with a stated on-page reason — that decision is **correct and must be retained**. The DST confirms there is no research claim to make.

### 29.4 Scope and delimitations

Use §5 (Scope) and §6 (Delimitations) verbatim in structure.

### 29.5 Significance

| Dimension | Defensible statement |
|---|---|
| Academic | Demonstrates end-to-end engineering of a telemetry analytics system: simulation, rule-based analytics, persistence, real-time delivery, access control and automated verification, with the boundary between simulation and physical reality stated explicitly. |
| Engineering | Provides a reproducible (seeded) testbed for iterating on fleet-analytics rules without hardware; the authorization-perimeter test makes the security model self-enforcing as the API grows. |
| Practical | Demonstrates how a fleet operator would consume the information (live dashboard, alerts, driver and health views). **Not** a production fleet-management tool; no claim of operational use. |

### 28.2 Internal contradiction inside one file

`README.md` is self-contradictory: its "Current Scope & Limitations" section
(lines 272–275) denies authentication, containerization and full REST integration,
while its "Future Direction" section (lines 289–291) marks **the same three items**
as *shipped*. This is the most damaging documentation defect found, because it is
visible without opening any other file.


| ID | Limitation |
|---|---|
| L-19 | **Docker runtime NOT VERIFIED** — daemon unavailable on the M5.3 host. Compose, Dockerfiles and the documented topology are configuration, not verified behaviour. |
| L-20 | `uvicorn --reload` on Windows emits asyncpg/CancelledError noise during shutdown; the supported lifecycle without `--reload` is clean |
| L-21 | No coverage tooling (no pytest-cov) and no load/benchmark suite |
| L-22 | API latency and concurrent-user capacity are NOT QUANTIFIED |
| L-23 | The development host ran PostgreSQL 18.4 while compose and CI pin 16 |


### 26.2 What the M5.3 acceptance run covered

Authentication and session lifecycle; RBAC across roles; Digital Twin
create/configure/activate/launch/run/stop; telemetry generation and persistence;
dashboard snapshot delivery over an authenticated WebSocket; alert pipeline;
seed reproducibility; simulation-speed effect on simulated time; duration-expiry
termination with a `completed` run row; a real console-interrupt shutdown with
complete log sequence and no tracebacks; restart with zero duplicate active
runners.

### 26.3 Committed test inventory

| Layer | Files | Notable coverage |
|---|---|---|
| Unit (`tests/unit/`) | 14 | safety scoring and its single source, scenario parameters, health reasons, driver statistics, trip/active-trip snapshot contracts, runtime resilience and stale-trip abort, vehicle runner peak speed |
| Integration (`tests/integration/`) | 11 | simulation controller, runtime shutdown, alert concurrency and lifecycle, fleet runtime, intelligence consumers and persistence, stale-trip persistence, brake-percent conversion, scenario assignments, active-trip invariant |
| API (`tests/api/`) | 22 | one file per router, plus `test_auth.py`, `test_authorization.py`, `test_authorization_perimeter.py`, `test_bootstrap_admin.py`, `test_digital_twin.py` (24 tests), `test_lifespan_shutdown.py`, `test_settings_integration.py`, `test_websockets.py` |
| Root (`tests/test_analytics_api.py`) | 1 | analytics endpoints |
| Frontend | 23 suites / 265 tests | adapters, utils, components, pages, auth guards, WebSocket client |

### 26.4 Caution

Test counts evidence that the suites pass; they are **not** evidence of overall
software quality, coverage percentage, or production readiness. No coverage
tooling is configured (C-V3).

| `/maintenance` | `Maintenance.jsx` | `ProtectedRoute` |
| `/settings` | `Settings.jsx` | `ProtectedRoute` + `RoleRoute(['admin'])` |
| `/digital-twin-lab` | `DigitalTwinLab.jsx` | `ProtectedRoute` + `RoleRoute(['admin'])` |
| `*` | redirect to `/dashboard` | — |

### 23.2 Architectural components

| Concern | Location |
|---|---|
| Routing + protection | `App.jsx`, `components/auth/ProtectedRoute.jsx`, `components/auth/RoleRoute.jsx` |
| Authentication state | `context/AuthContext.jsx`, `auth/tokenStorage.js` |
| Live data | `context/LiveDataContext.jsx` (merges REST hydration with WS snapshots) |
| Feature state | `context/FleetContext.jsx`, `TripsContext.jsx`, `TripDrawerContext.jsx`, `VehicleDrawerContext.jsx` |
| REST clients | `services/api/{vehicleApi,tripApi,driverApi,alertApi,maintenanceApi,telemetryApi,analyticsApi}.js` |
| Payload adapters | `services/driverAdapter.js`, `services/alertAdapter.js`, `utils/dashboard.js` |
| WebSocket client | `websocket/connectionManager.js` |
| Feature components | `components/{dashboard,fleet,drivers,trips,alerts,maintenance,vehicleHealth,analytics,ui,layout,shared,common,auth}` |
| Charts | `recharts` |

### 23.3 Verified properties

- **No mock data** in application source: a search for mock/dummy/placeholder across `frontend/src` (excluding tests) returned zero matches.
- 23 Vitest suites / 265 tests cover adapters, utils, components, pages and the auth guards.
- ESLint v10 runs as `npm run lint` in CI and passed clean in M5.3.
- `npm run build` produced a production bundle (2,593 modules) in ~24 s.

  score**, not competing algorithms.
- The M5.2 property "single canonical persisted driver safety score" is preserved.

### 20.4 Interpretation limits

The score is **rule-based and distance-normalised**. It is a fleet-simulation
metric. No claim of correlation with real-world crash risk, licensing standards
or insurance scoring may be made.

---

## 33. Chapter 5 Fact Sheet

Module → file mapping for the implementation chapter. All paths verified.

| Implementation area | Primary files |
|---|---|
| Application entrypoint | `backend/api/main.py` (FastAPI app, lifespan, WS router mounting, CORS) |
| Composition root | `backend/application/runtime.py` (`DriveVitalsRuntime`, tick loop, trip completion) |
| Simulation control | `backend/application/simulation_controller.py` |
| Simulation lifecycle state | `backend/api/simulation_state.py` |
| Fleet runtime | `backend/fleet/runtime/fleet_runner.py`, `vehicle_runner.py` |
| Fleet fixtures | `backend/fleet/config/fleet_config.py`, `fleet_factory.py` |
| Telemetry generation | `backend/telemetry/generators/obd_generator.py` |
| Telemetry model | `backend/telemetry/models/telemetry_sample.py` |
| Pipeline | `backend/pipeline/telemetry_pipeline.py`, `backend/streaming/snapshot_stream.py` |
| Behaviour analytics | `backend/analytics/behaviour/{detection,events,aggregation}` |
| Vehicle health | `backend/analytics/vehicle_health/` (engine, cooling, brakes, transmission, fuel system + `health_reasons.py`) |
| Driver statistics / safety | `backend/analytics/driver_statistics/` (`safety.py`, `config.py`, `driver_score_calculator.py`) |
| Maintenance | `backend/maintenance/` (`estimators/`, `estimation/rules.py`) |
| Alerts | `backend/alerts/` (`alert_engine.py`, `generators/`, `deduplication.py`, `alerts_config.py`) |
| Dashboard assembly | `backend/dashboard/services/dashboard_builder.py`, `dashboard/schemas/dashboard_payload.py` |
| Trip snapshots | `backend/trips/services/{trip_builder,active_trip_builder}.py` |
| Persistence | `backend/db/persistence_service.py` |
| Models / repositories / migrations | `backend/db/models/` (16), `backend/db/repositories/` (16), `backend/db/migrations/versions/` (16) |
| REST API | `backend/api/v1/routers/` (14), `schemas/`, `services/`, `dependencies.py` |
| Authentication | `backend/api/security.py`, `backend/api/v1/services/auth_service.py`, `admin_bootstrap.py` |
| WebSocket layer | `backend/api/websocket/{manager,security,dashboard,trips,alerts,snapshot_publisher,trip_publisher}.py` |
| Frontend entry / routing | `frontend/src/main.jsx`, `App.jsx` |
| Frontend auth | `frontend/src/context/AuthContext.jsx`, `auth/tokenStorage.js`, `components/auth/{ProtectedRoute,RoleRoute}.jsx` |
| Frontend live data | `frontend/src/context/LiveDataContext.jsx`, `websocket/connectionManager.js` |
| Frontend API adapters | `frontend/src/services/api/*.js`, `services/{driverAdapter,alertAdapter}.js` |
| Frontend pages | `frontend/src/pages/` (13 pages incl. Digital Twin Lab and Settings) |
| Frontend components | `frontend/src/components/` (14 feature folders + `ui/`, `layout/`) |
| Tests | `tests/{unit,integration,api}/`, `tests/test_analytics_api.py`, `frontend/src/**/*.test.js(x)` |
| CI | `.github/workflows/ci.yml` |
| Containers | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` |

---

---

## 34. Diagram Inventory

Recommended **minimal** set that satisfies a UOL-style structure without redundancy.

| Diagram ID | Chapter | Diagram | Source components | Evidence | Recommendation |
|---|---|---|---|---|---|
| D-01 | Ch 1 | System context (optional) | DriveVitals, actors, PostgreSQL, browser | §3, §9, §25 | Optional; useful for Ch 1 but not required |
| D-02 | Ch 3 | Use case diagram | §9 actors + §13 use cases | §9, §13 | **Required** — must not include internal components as actors |
| D-03 | Ch 4 | System architecture (layered) | §16 layers | §16 | **Required** |
| D-04 | Ch 4 | ERD | 18 entities, §15 cardinalities | §14, §15 | **Required** — omit any Run→Trip FK edge |
| D-05 | Ch 4 | Class diagram | ORM aggregates (§32) | `backend/db/models/`, §15 | Recommended; do not attempt all 16 models |
| D-06 | Ch 4 | Sequence: authentication + WebSocket connect | §10.1, §10.5, §22.3 | §10, §22 | **Required** |
| D-07 | Ch 4 | Sequence: Digital Twin launch | §17.1 chain | §17, FR-SIM-01 | **Required** |
| D-08 | Ch 4 | Sequence: telemetry flow (time-ordered) | §18.1 | §18 | **Required** |
| D-10 | Ch 4 | DFD Level 0 | §16.2 + external entities | §16.2 | **Required** |
| D-11 | Ch 4 | DFD Level 1 | processes: generation, analytics, persistence, delivery | §18, §19, §21, §22 | **Required** |
| D-12 | Ch 4 | DFD Level 2 | decompose the analytics process | §19 | Include only if it adds information; otherwise omit |
| D-13 | Ch 5 | UI screenshots (login, dashboard, Digital Twin Lab, settings) | React pages | `frontend/src/pages/` | **Required** — must show the real running system |

**Redundancy warnings:** D-08 and D-11 overlap. If both are drawn, make D-08 a
*sequence* (time-ordered) and D-11 a *DFD* (data movement) — never the same picture
twice. D-12 must add information or be dropped; a Level 2 that merely renames Level 1
boxes is redundant.

## 35. UOL Structure Alignment

The UOL chapter structure is the documentation target. Content must be written from
the mapped sections, not from memory.

| UOL chapter | DST sections supplying the content |
|---|---|
| **Ch 1 Introduction** — 1.1 Problem Statement | §29.1 |
| 1.2 Objectives | §29.2 (OBJ-01…OBJ-08) |
| 1.3 Research Hypothesis/Questions | §29.3 — **omit with stated reason** (product-based track; Draft 0.1 already does this) |
| 1.4 Scope and Delimitations | §5, §6 |
| 1.5 Significance | §29.5 |
| **Ch 2 Literature Review** — strategy, existing/commercial systems, academic work, comparative analysis, gap, proposed solution | §30 (categories, dimensions, gap framing, and the strict separation of implementation facts from literature still to be researched) |
| **Ch 3 System Requirements** — environment, interfaces, constraints, assumptions, FRs, NFRs, use cases | §31 → §25, §16.2, §8, §7, §11, §12, §9, §13 |
| **Ch 4 System Design** — architecture, ERD, class diagram, sequence diagrams, activity diagrams, DFD 0/1/2 | §32, §34, §14, §15, §16, §17, §18, §21, §22 |
| **Ch 5 Implementation** — development environment, technology stack, module descriptions, UI implementation | §25, §24, §33, D-13 |

Presentation must remain technically professional and internationally readable; UOL
numbering is a structure, not a constraint on language or tone.

---

---

## 36. Requirement Traceability

Representative traces. Each runs Problem → Objective → FR → Use case → Component →
Module → Test.

### Trace 1 — Controlled, reproducible simulation

| Level | Item |
|---|---|
| Problem | Fleet data is unavailable without physical vehicles (§29.1) |
| Objective | OBJ-01, OBJ-02 |
| Functional requirement | FR-SIM-01 launch a scenario; FR-SIM-04 seed reproducibility; FR-SIM-05 speed |
| Use case | UC-04 Configure and launch a scenario; UC-05 Stop or expire a run |
| Architecture | `SimulationController`, `FleetRunner`, `VehicleRunner`, `OBDGenerator` (§17.1) |
| Implementation | `backend/application/simulation_controller.py`, `backend/fleet/runtime/*`, `backend/telemetry/generators/obd_generator.py` |
| Verification | `tests/integration/test_simulation_controller.py`, `tests/unit/test_scenario_parameters.py`, M5.3 acceptance checks 27–33 |

### Trace 2 — Driver safety assessment

| Level | Item |
|---|---|
| Problem | Driver behaviour is observed after the fact, not continuously (§29.1) |
| Objective | OBJ-03 |
| Functional requirement | FR-ANL-01 detect behaviour; FR-ANL-03 canonical safety score; FR-ANL-04 grade |
| Use case | UC-07 Review driver performance |
| Architecture | `AnalyticsEngine` → behaviour detection → trip summary → `compute_safety_score` (§19.1, §19.2, §20) |
| Implementation | `backend/analytics/behaviour/`, `backend/analytics/driver_statistics/safety.py`, `backend/trips/services/trip_builder.py` |
| Verification | `tests/unit/test_safety_scoring.py`, `test_safety_score_sources.py`, `tests/integration/test_intelligence_persistence.py` |

### Trace 3 — Access control

| Level | Item |
|---|---|
| Problem | Operational and configuration data must not be openly mutable |
| Objective | OBJ-07 |
| Functional requirement | FR-AUTH-01…08, FR-RBAC-01…07 |
| Use case | UC-01 Authenticate, UC-02 Log out, UC-03 Manage fleet fixtures, UC-11 Settings |
| Architecture | `get_current_user` → `require_role` guards; WebSocket `authenticate_ws` (§10) |
| Implementation | `backend/api/security.py`, `backend/api/v1/dependencies.py`, `backend/api/websocket/security.py`, `frontend/src/components/auth/` |

### Trace 4 — Live operational visibility

| Level | Item |
|---|---|
| Problem | Fleet state must be observable while it is happening (§29.1) |
| Objective | OBJ-06 |
| Functional requirement | FR-WS-01…04, FR-UI-01 |
| Use case | UC-06 Monitor the live dashboard, UC-12 View live telemetry |
| Architecture | Publisher → queue → worker → `WebSocketManager` → `LiveDataContext` (§22) |
| Implementation | `backend/api/websocket/*`, `backend/dashboard/services/dashboard_builder.py`, `frontend/src/context/LiveDataContext.jsx`, `frontend/src/websocket/connectionManager.js` |
| Verification | `tests/api/test_websockets.py`, `tests/unit/test_trip_snapshot_contract.py`, frontend WebSocket and context suites |

### Trace 5 — Data integrity

| Level | Item |
|---|---|
| Problem | Persisted operational data must remain trustworthy (§29.2 OBJ-05) |
| Objective | OBJ-05 |
| Functional requirement | FR-VEH-02 unique conflict → 409; FR-ANL-06 unknown health persists as NULL |
| Use case | UC-03 Manage fleet fixtures |
| Architecture | Unique indexes + `IntegrityError` translation + nullable scores without server default (§14, §16.1) |
| Implementation | `digital_twin_service.py::_translates_conflicts`, migration `b7d1f3a9c2e5` |
| Verification | `tests/api/test_digital_twin.py` (409 tests), fresh-database migration check, `tests/unit/test_health_reasons.py` |

## 37. Terminology Lock

Binding definitions for Chapters 1–9. The "avoid" column lists wording that must not appear.

| Preferred term | Definition | Terms to avoid | Reason |
|---|---|---|---|
| **DriveVitals** | The system described in this document | — | official product name |
| **Digital Twin** | The persisted, admin-configurable fleet model plus its deterministic generator and run lifecycle | "physically accurate twin", "digital replica of a real vehicle", "physics-accurate simulation" | no physical equivalence is claimed or implemented |
| **Synthetic telemetry** | Measurements produced by `OBDGenerator` from vehicle parameters and a seeded RNG | "real telemetry", "live vehicle data", "measured data" | no physical source exists |
| **Simulation scenario** | A persisted configuration (seed, speed, duration, assignment set) defining a run | "test case", "job" | matches `simulation_scenarios` |
| **Simulation run** | One execution of a scenario, recorded in `simulation_runs` | "simulation job", "task" | matches `simulation_runs` |
| **FleetRunner** | The component holding and advancing all active `VehicleRunner`s | — | class name |
| **VehicleRunner** | The component driving one vehicle's generator tick by tick | — | class name |
| **Telemetry sample** | One generated observation (`TelemetrySample`) | "data point from the vehicle" | no physical source |
| **Driver behaviour analytics** | Threshold-based detection of speeding, harsh braking, aggressive throttle, high RPM | "AI behaviour detection", "ML driver model" | rule-based only |
| **Safety score** | The single distance-normalised exponential score in `safety.py`, 0–100 | "risk score", "driver rating" | one canonical definition only |
| **Vehicle health** | Weighted aggregate of five subsystem scores | "vehicle condition score (AI)", "predicted health" | rule-based, current-state only |
| **Alert** | A deduplicated record of a rule condition with lifecycle and resolution | "incident", "warning (AI)" | matches the `alerts` entity |
| **Trip** | One journey of a vehicle by a driver on a route | "route", "session" | three distinct entities exist |
| **RBAC** | Role-based access control with viewer / operator / admin | "permissions" | matches implementation |
| **WebSocket** | A persistent connection used here for server push | "real-time API", "socket.io channel" | native WebSockets |
| **Persistence** | Writing operational state to PostgreSQL through repositories | "storage layer (NoSQL)" | relational only |
| **Dashboard snapshot** | The assembled live fleet payload broadcast each tick | "live data feed", "stream" | matches `dashboard_snapshot` |
| **Anonymous read** | A deliberately public operational read endpoint | "unauthenticated access (defect)", "unsecured API" | it is a *policy*, enforced by a test |
| **Rule-based** | Deterministic threshold/formula evaluation | "AI-powered", "intelligent", "smart", "predictive" | no learning exists |
| **Measured** | A value obtained by running the system | "estimated performance", "expected" | separates evidence from assertion |

### 37.1 Banned vocabulary

Do not use: cutting-edge, revolutionary, AI-powered, smart, advanced, highly
scalable, enterprise-grade, real-world accurate, state-of-the-art, seamless,
powerful — unless used in a plain technical sense and immediately grounded in evidence.

---

---

## 38. Do Not Claim

The following are **false of this system** and must never appear in any chapter, slide or defence:

1. DriveVitals is not an AI system.
2. DriveVitals is not an ML system; no model is trained, loaded or inferred.
3. DriveVitals does not consume real CAN data.
4. DriveVitals does not consume real OBD-II / ELM327 hardware data.
5. DriveVitals does not represent a physically accurate vehicle twin.
6. DriveVitals is not a production fleet deployment and is not used operationally.
7. DriveVitals is not a cloud-native or microservice architecture; it is one Python process.
8. DriveVitals does not use Kafka, Redis, Celery or any broker/cache/task queue.
9. DriveVitals does not perform predictive maintenance; it applies current-state rules.
10. DriveVitals does not detect driver fatigue, distraction or driver identity.
11. DriveVitals has no GPS, geofencing or route-optimisation capability.
12. DriveVitals provides no reports or data export.
13. DriveVitals does not support cloud deployment or multi-tenancy.
14. The Docker/Compose stack is **not verified**; it is configuration only.
15. The safety score is not validated against real-world crash or insurance data.
16. The system is not "scalable" or "production-ready"; it is a single-process demonstrator.
17. There is **no research hypothesis**; the project is product-focused.
18. Novelty is not claimed; the techniques used are established practice (§30.3).

---

## 39. Open Questions / Unverified Items

| ID | Question | Why it matters | Suggested resolution |
|---|---|---|---|
| Q-01 | What is the official university-registered project title and declared area? | Title page, front matter, Chapter 1 | Obtain from the supervisor/registry; not derivable from the repository |
| Q-02 | Student name(s), registration number(s), degree title, supervisor name, session | Front-matter placeholders | Administrative; not in the repository |
| Q-03 | Must the abstract be final at Draft 0.1, or may it be updated with the M5.3 results? | Abstract accuracy | Confirm the handbook requirement; this DST now supplies final verified figures |
| Q-04 | Why does the long-lived development database lack the server defaults the migration chain creates on `vehicle_statistics`? | Reproducibility claim (C-08) | Inspect how that database was first created (likely model metadata rather than a clean migration replay). A fresh database matches the migration chain, so the chain is authoritative. |
| Q-05 | Which PostgreSQL version will be declared — 16 (compose/CI) or 18.4 (tested host)? | Environment accuracy | Declare 16 as the reference and note the tested host, or re-verify on 16 |
| Q-06 | Should `docs/design/*`, `docs/team/*` and `docs/Project_Bible/*` be archived or annotated? | Contradiction risk (C-10, C-11) | Annotate as historical; the code is the reference |
| Q-07 | Are the three existing citations sufficient for Chapter 2, or must the comparison set be researched further? | Chapter 2 validity | Perform the research listed in §30.4 before finalising Chapter 2 |
| Q-08 | Was any user study, usability evaluation or accessibility audit intended? | NFR-USA-02 remains NOT QUANTIFIED | If none, keep NOT QUANTIFIED; never invent usability metrics |
| Q-09 | Should `vehicle_statistics` be removed, or populated by the application? | Schema vs. reality (L-11) | Engineering decision outside a feature-frozen release; document as a limitation meanwhile |
| Q-10 | Can the Docker stack be verified on a host with a running daemon before submission? | Removes constraint L-19 | Run `docker compose up --build` and the backend suite inside the backend container |

---

## 40. Extraction Method and Integrity Statement

**What was inspected.** The complete tracked repository at `b8864f2` — backend 237
Python files; 14 routers; 16 ORM models; 16 repositories; 16 migrations; the
frontend `src/` tree with 16 pages and 14 component folders; 48 backend test files;
23 frontend suites; `docker-compose.yml`; two Dockerfiles;
`.github/workflows/ci.yml`; `.env.example`; `requirements.txt`; `package.json` —
plus **live runtime evidence**: the running API's OpenAPI inventory, the live
development database queried through `information_schema`, a fresh-database
migration replay, a scripted comparison of the migrated schema against the
development database, a fresh 45-check end-to-end acceptance run, and a real
console-interrupt shutdown.

**What was not done.** No application code, migration, test or configuration was
modified. No existing FYP file was altered or overwritten. No document listed in §28
was rewritten. No chapter text was produced.

**Integrity statement.** Every fact above is traceable to a file, test, live query or
measurement. Where a source disagreed with the implementation, the implementation won
and the disagreement was recorded in §28 rather than silently discarded. Items that
could not be established are listed in §39 and marked `UNVERIFIED`.

**Chapters 1–5 must not be written until this DST is reviewed and the items in §39 are
either resolved or explicitly accepted as limitations.**

