# Alerts Page — Product / UX Audit

**Scope:** Read-only product/UX audit of the Alerts surface. Target bar: Motive / Samsara / Geotab, and DriveVitals' own mature Trips, Vehicle Health, and Drivers surfaces. The page must read like an **enterprise fleet incident command center**, not a database dump.

**Date:** 2026-08-15 · **Status:** Audit complete, no code changed.

---

## 1. Executive Summary

The Alerts page has the right raw materials — a canonical data contract, live websocket feed, idempotent ack/resolve, a real incident-carrying backend model — but it renders as a **wall of cards** and a set of **mutually inconsistent KPIs**. A fleet manager cannot currently answer the four questions a command center must answer:

1. **What needs my attention right now?**
2. **Which vehicles/drivers are at risk?**
3. **What happened, how severe is it, and what do I do?**
4. **Is this live or historical?**

Five concrete problems dominate, in priority order:

- **P-1 (Data trust): The KPI strip and the severity donut count different populations.** KPI says **Critical 8 / High 17**; the donut says **Critical 6 / High 11**. The strip counts severity across *all* lifecycle states; the donut counts only *active* alerts by severity and separately lumps *all* 27 resolved alerts (of every severity) into one "Resolved" slice. Same data, two answers, on one screen. *(Verified in `frontend/src/utils/alerts.js`: `computeAlertKpis` vs `computeSummaryDistribution`.)*
- **P-2 (Data trust): 52% of alerts render as "Other".** 32 of 61 rows have a NULL `category` — these are pre-migration rows whose `category`/`condition`/`message` columns were never backfilled. The chart's `category_label || 'Other'` fallback then mislabels legacy data-debt as a real category. *(Verified against `drivevitals_dev`; root cause is data, not taxonomy.)*
- **P-3 (Live vs historical): 10-day-old alerts render as if they were live.** Verified in `drivevitals_dev`: **33 of 34 "active" alerts are > 72 h old (oldest 2026-08-05 17:48, ≈ 236 h); only 1 is fresh.** The page renders all of them with equal visual weight and feeds them into the "Critical 8 / Active 34" strip. A command center cannot show stale rows as live.
- **P-4 (Incident model): one bad trip produces five separate alerts.** The trip generator fires one alert per rule (`trip_unsafe`, `trip_aggressive_driving`, `trip_repeated_harsh_braking`, `trip_repeated_harsh_acceleration`, `trip_overspeeding`) for the same vehicle/trip/evidence. The page then lists four near-duplicate cards. It should be one incident with signal chips. *(Verified in `backend/alerts/generators/trip_alerts.py`.)*
- **P-5 (IA): seven overlapping surfaces with no hierarchy.** Live Alert Feed, Alert Summary donut, Alert Distribution donut, Most Affected Vehicles, Critical Incident Queue, Alert Timeline, Live Driving Events are stacked as peers. There is no "LIVE NOW" vs "ALERT HISTORY" separation and no single scan path.

**The fix is mostly frontend, and the audit proposes it (Sections 15–18):** adopt the five-level IA, replace the card wall with an enterprise table feed, reconcile every KPI to one canonical population, visually separate live vs historical, group trip alerts client-side into incidents, and reframe the drawer as a "command panel" that answers WHAT/WHY/WHO/WHERE/WHEN/SEVERITY/STATUS/EVIDENCE/WHAT-SHOULD-I-DO.

**Backend follow-ups (Phase 2, out of scope for the frontend P0–P6 roadmap):** backfill legacy rows (`category`, `condition`, `message`), introduce an `incident_id`, schedule `resolve_stale` so the server can't leave week-old alerts active.

---

## 2. Current-State Information Architecture

What the page renders today, top to bottom (composition in `frontend/src/pages/Alerts.jsx`):

| # | Surface | Component | Live data? | Notes |
|---|---------|-----------|------------|-------|
| 1 | Header | Alerts header | — | Title + subtitle |
| 2 | KPI strip | `AlertKpiCards` | ✓ | Critical, High, Active, Acknowledged, Resolved |
| 3 | Filters | `AlertFilters` | ✓ | severity / category / time range |
| 4 | Summary donut | `AlertSummaryChart` | ✓ | severity buckets + "Resolved" slice |
| 5 | Distribution donut | `AlertDistribution` | ✓ | by category |
| 6 | Most affected | `MostActiveVehicles` | ✓ | per-vehicle counts |
| 7 | Critical queue | `CriticalIncidentQueue` | ✓ | critical/high + active only |
| 8 | Live events | `DrivingEventsFeed` | ✓ (WS) | per-vehicle behaviour events |
| 9 | Timeline | `AlertTimeline` | ✓ | time-series of alerts |
| 10 | Feed | `LiveAlertFeed` | ✓ (WS) | card list, newest first |

Problems with the IA:

- No **attention hierarchy** — the "what do I do right now" surface (queue) is pushed below two donuts.
- No **live vs historical separation** — the LIVE EVENTS feed and the 10-day-old alert cards share the same page weight and same "ACTIVE" styling language.
- **Redundancy:** the severity donut, the KPI strip, and the queue all re-express severity; the distribution donut, most-affected list, and feed all re-express vehicles.
- **No search, no sort, no pagination on the feed** — it is a capped card list, not a record.
- **Filter scope is ambiguous:** filters apply to the feed; the KPIs/donuts do not re-derive from the filtered set in a way the user can trust (see Section 4).

---

## 3. Product Problems (per the product questions)

| Product question | Current answer | Verdict |
|---|---|---|
| What needs attention now? | "Critical 8" strip + queue | Partial — but "Critical 8" includes resolved rows; no *unacknowledged* signal |
| Which vehicles/drivers are at risk? | Most-affected vehicles list | Partial — driver not surfaced; severity not aggregated by vehicle |
| What happened, why, how severe? | Card title + drawer | Partial — legacy rows have no `message`/`condition`/`category`; drawer reads "None" |
| Live vs historical? | No visual distinction | Failing |
| Acknowledged or not? | "Acknowledged 1" KPI | Weak — a state, not an action count; only 1 row in the dataset uses it |
| What should I do? | Drawer has ack/resolve | Partial — no "next step" guidance, no vehicle/driver/trip navigation from feed rows |
| Fleet patterns? | Two donuts | Weak — donuts show one slice per record, not trend |

Additional product gaps:

- **No incident grouping:** one trip → up to 5 alerts (Section 6).
- **No "risk" aggregation:** a vehicle with 3 open medium alerts and one with 1 critical alert look identical in the "most affected" list (both count = N).
- **No empty/stale states:** a fresh DB shows empty donuts; a stale DB shows everything as live.
- **No connection indicator:** the page never states whether the websocket is up (only the events feed implies it).

---

## 4. KPI Problems — Reconciliation

**Ground truth (`drivevitals_dev`, 61 alerts):**

| Severity | Active | Resolved | Total |
|----------|-------:|---------:|------:|
| Critical | 6 | 2 | 8 |
| High | 11 | 6 | 17 |
| Medium | 17 | 8 | 25 |
| Low | 0 | 11 | 11 |
| Info | 0 | 0 | 0 |
| **Total** | **34** | **27** | **61** |

**What each surface renders:**

| Surface | Critical | High | Active | Ack'd | Resolved | Population |
|---|---|---|---|---|---|---|
| KPI strip | 8 | 17 | 34 | 1 | 27 | raw field counts, **any lifecycle** |
| Summary donut | 6 | 11 | 17 | — | 27 | **active only** by severity + resolved lump |

**Root cause (code):**
- `computeAlertKpis` (`frontend/src/utils/alerts.js`) counts raw fields across all rows: `severity === 'critical'` ⇒ 8, `status === 'active'` ⇒ 34, `acknowledged === true` ⇒ 1, `status === 'resolved'` ⇒ 27.
- `computeSummaryDistribution` buckets **active** alerts by severity (6/11/17/0/0) and adds a separate `resolved` slice counting all resolved regardless of severity (27).

**Consequences:**
- "Critical 8" and "Critical 6" disagree **on the same screen**. This is the single biggest data-trust violation.
- The donut's "Resolved" slice mixes severities — a resolved critical and a resolved low weigh the same.
- The strip's "Acknowledged 1" is nearly meaningless as a top-level metric (it is a drawer state; the actionable number is *unacknowledged*).

**Latent trap:** the backend `/api/v1/alerts/stats` (`backend/api/v1/services/alert_service.py:119`) returns keys `critical_active` / `high_active` but the SQL filters only `severity`, **not** `status`. The label lies. The frontend does not call `stats()` today, but anyone wiring it later inherits the bug. Fix the label or the filter in Phase 2.

**Rule going forward (DoD):** *No KPI may independently calculate a different population.* All KPIs/charts derive from one canonical query (default: active-only, severity-bucketed), and "resolved" is always a sub-count of the same set, never a third population.

**Recommended strip (see also Section 15):** Critical (active), High (active), **Unacknowledged** (active & !acknowledged), Active (total), Resolved (last 24 h). Every number is clickable and filters the feed.

---

## 5. Incident vs Alert vs Event Model

Today there are two tiers in the data:

- **Event** — behaviour telemetry (`harsh_braking`, `aggressive_throttle`, `speeding`), emitted live per vehicle (`active_event_types`, keyed `vehicle:event_type`, no timestamps). Not persisted as alerts.
- **Alert** — a persisted row with a canonical `alert_id`, `severity`, `category`, `condition`, `evidence`. One row per *condition*, not per *occurrence* (upsert keyed `scoped:vehicle`; repeated occurrences after resolution get a truncated-`-suffix` id).

**There is no incident tier.** Verified fan-out in the live dataset and the generator:

- `trip_alerts.py` fires up to **5 separate alerts** for one trip when counts cross thresholds: `trip_overspeeding` (Medium), `trip_repeated_harsh_braking` (Medium), `trip_repeated_harsh_acceleration` (Medium), `trip_aggressive_driving` (High), `trip_unsafe` (Critical). All share `vehicle_id`, `trip_id`, and the same `evidence.event_counts` block.
- The user-observed example — *unsafe trip 134 events / aggressive 54 severe / harsh braking 54 / harsh acceleration 78* — is **one bad trip rendered as four cards**.

**Recommendation — three-tier model:**

1. **Event** — raw behaviour signal (unchanged).
2. **Incident** — one logical occurrence (one trip event, one telemetry spike, one maintenance due). Owns the "story": time, vehicle, driver, trip, max severity, involved signals.
3. **Alert** — one condition *signal* under an incident (e.g., incident "unsafe trip V-103 08-05" has signals: 134 events, 54 severe, 54 braking, 78 acceleration).

**Frontend-only interim (P3 of the roadmap, no contract change):** group feed rows client-side by `vehicle_id + trip_id + day`, render ONE card per incident with signal chips from `evidence.event_counts`; severity = max child severity; the drawer lists child conditions. This immediately kills the four-cards-one-trip problem without a backend migration. The true `incident_id` column is Phase 2 backend work.

---

## 6. Category Taxonomy

**Current canonical set** (`backend/alerts/models/fleet_alert.py` + `alerts_config.py`): `safety_driving`, `vehicle_health`, `cooling`, `fuel`, `engine`, `electrical`, `transmission`, `brakes`, `maintenance`, `trip` (alert *type*), plus `other` fallback via `category_for()`.

**Rendered distribution vs ground truth:**

| Category | Rendered | DB count | Explanation |
|---|---|---|---|
| Other | 32 (52%) | 32 NULL | **legacy rows, category never backfilled** |
| Safety & Driving | 19 (31%) | 19 | trip_* generator rows ✓ |
| Maintenance | 10 (16%) | 10 | maintenance_* generator rows ✓ |

**Findings:**
- The "Other" 52% is **data debt, not taxonomy** — 32 pre-migration rows have NULL `category`/`condition`/`message`. The chart's `category_label || 'Other'` fallback (`AlertDistribution.jsx` / `utils/alerts.js`) converts NULL into a fake category.
- For NULLs, render **"Unclassified"** (muted), never "Other" — so data debt is visible as debt.
- Proposed canonical taxonomy for Phase 2 (keep the enum stable, only *label* it): Safety & Driving · Maintenance · Engine · Cooling · Fuel · Electrical · Transmission · Brakes · Vehicle Health · Information. (Optionally split "Safety & Driving" into Behaviour vs Overspeed later; do not do it now.)
- **Backfill migration (Phase 2):** set `category`, `condition`, `message` on the 32 legacy rows from their `alert_id` via `category_for()`; set `message` from a per-`condition` vocabulary table. Until then, the frontend shows "Unclassified" for those rows.

---

## 7. Live vs Historical Model

**Problem observed:** **33 of 34 "active" alerts are > 72 h old** (oldest active `2026-08-05 17:48`, ≈ 236 h); only 1 is fresh. The page renders all 34 with identical visual weight, and the "Critical 8 / High 17" strip and donut make no age distinction. A 10-day-old trip alert reads as a live incident.

**Findings:**
- `AlertRepository.resolve_stale` exists and resolves open alerts whose condition leaves the current snapshot — but it only runs while the alert engine ticks. When the server is down (as during this audit), the server can leave week-old rows `status='active'`; on restart they are re-flagged by the next snapshot, but nothing enforces it on a schedule.
- The frontend has no staleness degradation at all.

**Model to adopt:**
- **Live** = actively re-emitted by the engine (upsert keeps the row `active`) or < threshold age (recommend 24 h).
- **Stale** = `status='active'` but older than threshold (or engine-silent). Render muted, no pulse, grouped at the bottom, excluded from the KPI strip (strip shows only LIVE + genuinely active).
- **Historical** = `status='resolved'`; in the table behind the History view.

**Frontend rules (DoD):** no alert older than 24 h may use the live pulse or the top-strip; "LIVE NOW" is reserved for websocket-verified activity; the page shows a connection state. **Backend (Phase 2):** a periodic `resolve_stale`/staleness sweep independent of the simulation, so the DB cannot hold week-old "active" alerts.

---

## 8. Alert Feed Recommendation

Replace the card wall with an **enterprise table** (Motive/Samsara style) as the single record surface:

| Time | Vehicle | Driver | Incident | Category | Severity | Status | Evidence | Action |
|---|---|---|---|---|---|---|---|---|
| 08-05 11:36 | V-103 | — | Unsafe trip · 134 events | Safety & Driving | ● Critical | Active | 134 ev · 54 sev | Ack / Open |

- **Columns:** time (relative + absolute), vehicle (link → Vehicle drawer), driver (link when present), incident title (grouped, Section 5), category chip, severity badge, status badge, evidence (compact chips), row actions.
- **Sorting:** severity → created_at desc (default). **Filters:** existing severity/category/time-range filters remain and now visibly drive the table count. **Pagination or virtualized scroll** (≥ ~100 rows expected).
- **Status tabs:** Active (default) / Acknowledged / Resolved / All — the top-level "LIVE NOW vs ALERT HISTORY" split.
- **Row density:** compact table tokens; resolved rows muted; stale-active rows visibly downgraded (Section 7).
- **Interim:** keep `AlertCard` as the row's mobile/compact representation and inside the drawer's "related alerts" list — do not remove the component; stop using it as the page's primary list.

---

## 9. Critical Incident Queue Recommendation

`CriticalIncidentQueue` is already correct in scope (critical/high **and** active only). Keep it, reposition it, and tune:

- **Position:** directly under "Attention Required" (Level 2 of the IA), before the donuts.
- **Behavior:** it is the default tab of the table, pre-filtered to `severity in (critical, high) AND status == active AND !acknowledged`, newest first. Clicking a card scrolls the table to that row.
- **Exclude stale** (Section 7) unless the stale row is acknowledged-hidden; a stale critical must still appear but with the stale treatment + "engine silent" hint.
- Do **not** add "Avg Response Time" or other metrics that would require new backend computation.

---

## 10. Drawer Recommendation

Reframe `AlertDrawer` as a **command panel** with four zones (existing ack/resolve and `useVehicleDrawer` wiring stays):

1. **Header** — WHAT/WHEN/SEVERITY/STATUS: incident title, vehicle + driver, severity badge, status badge, category chip, absolute + relative time. No fabricated fields — legacy rows with NULL `message` must show "No message recorded" (muted), never an invented sentence.
2. **Why** — WHAT SHOULD I DO: `message` + `condition`; `evidence` rendered as typed chips (`event_counts`, threshold values, per-subsystem health status). For maintenance rows, a single clear CTA: "View maintenance" → Maintenance page filtered to the vehicle (Section 12).
3. **Related** — WHO/WHERE: sibling alerts for the same vehicle/trip (incident group, Section 5); links: View Vehicle (Vehicle drawer), View Driver (driver drawer when `driver_id`), View Trip (Trip drawer when `trip_id`).
4. **Actions** — Ack / Resolve (idempotent, existing repository contract), plus status-change feedback. Acknowledged ≠ Resolved must stay visually distinct (amber vs muted).

---

## 11. Timeline Recommendation

`AlertTimeline` today renders the same alerts already visible in the feed/donuts — it adds no decision value and occupies scarce vertical space. **Recommendation: remove the standalone timeline from the page.** Preserve the timeline's time-series visualization **inside the drawer** (related alerts for the incident/vehicle over time) where it explains *context*, not *inventory*. This honors the standing rule: *do not preserve components merely because they exist.*

If removed, delete `AlertTimeline.jsx` usage and its page wiring (component file can stay until the drawer variant lands).

---

## 12. Maintenance Boundary

**Rule:** Alerts surface maintenance **as a warning + action**, never as a record store.

- Alert layer: `maintenance_*` conditions emit alerts with severity derived from maintenance priority (`alerts_config._PRIORITY_SEVERITY`), category `maintenance`. (Verified: 10 maintenance rows, severities low→high.)
- The **Maintenance page owns** schedules, due dates, and history. The Alerts page must not duplicate them.
- **Drawer CTA** for a maintenance alert → navigate to Maintenance page pre-filtered to the vehicle. No maintenance-scheduling controls inside the Alerts page.
- The "Maintenance due" warning is a good *fleet pattern* signal for the intelligence section (Section 15, Level 3) — e.g., "3 vehicles due for brake inspection".

---

## 13. Vehicle / Driver / Trip Drill-Down Model

Every alert row already carries the keys (`alert_repository.upsert` stores `driver_id`, `trip_id`; evidence stores `vehicle_id` + `trip_id`). Wire them:

- **Row → Vehicle** → `useVehicleDrawer` (exists) — vehicle health, last trip, open alerts.
- **Row → Driver** → driver drawer (exists) — driver's incident history; render only when `driver_id` is present (trip alerts carry it; telemetry alerts may not).
- **Row → Trip** → `useTripDrawer` / trip route (exists) — trip detail + behaviour events (the 134 events live here).
- **Empty states:** columns/cells with no link render as "—", never as a broken link.

Depth rule: one level of context per click (alert → entity), never a chain of nested drawers.

---

## 14. Visual Design Recommendations

- **Five-level hierarchy** visually: (1) command header → (2) attention strip → (3) intelligence panel → (4) LIVE NOW band → (5) alert table. Each level has a distinct visual frame.
- **LIVE NOW band:** red-accent border frame + connection dot (green pulse when WS up, grey/red when down), containing `DrivingEventsFeed` only — the *only* surface allowed a live pulse.
- **Severity:** red / amber / blue / muted-green / grey, single token set (existing `SeverityBadge` colors). **Status:** green=active, amber=acknowledged, muted=resolved (existing `AlertStatusBadge`).
- **Stale rule:** any active alert > 24 h renders with reduced opacity, no pulse, and a "STALE" micro-badge; > 72 h collapses into the table's default views.
- **Numbers:** every KPI is a link into a pre-filtered table; every chart title states its population ("Active alerts by severity", not "Severity").
- **No card-wall:** replace stacked cards with the table (Section 8) + compact queue strip (Section 9). Cards remain only in the drawer's related list.
- Use existing app tokens (`--color-*`), same typography scale as Trips/Vehicle Health/Drivers so the page is unmistakably the same product.

---

## 15. Proposed Final IA

```
┌─────────────────────────────────────────────────────────────┐
│ 1  COMMAND HEADER                                            │
│    Alerts   ● live   [connection state]   [Last sync: 11:42] │
├─────────────────────────────────────────────────────────────┤
│ 2  ATTENTION REQUIRED                                        │
│    KPI strip (clickable): Critical 6 · High 11 ·            │
│    Unacknowledged 33 · Active 34 · Resolved(24h) 0           │
│    Critical Incident Queue (critical+high, active)           │
├─────────────────────────────────────────────────────────────┤
│ 3  FLEET ALERT INTELLIGENCE                                  │
│    Most affected vehicles (severity-weighted)                │
│    Categories (active only, "Unclassified" for NULL)         │
├─────────────────────────────────────────────────────────────┤
│ 4  LIVE NOW   [red frame · pulse allowed here only]          │
│    Live driving events (websocket)                           │
├─────────────────────────────────────────────────────────────┤
│ 5  ALERT HISTORY  [table feed]                               │
│    Tabs: Active | Acknowledged | Resolved | All              │
│    Filters · sort · pagination · severity/status/category    │
└─────────────────────────────────────────────────────────────┘
```

Removals: standalone timeline (→ drawer, Section 11), redundant severity donut (KPIs + queue carry it), "Acknowledged" as a top KPI (→ state filter), the card-wall feed.

---

## 16. Proposed Component Hierarchy

```
AlertsPage
├── CommandHeader            (title, connection dot, last-sync)
├── AttentionRequired
│   ├── AlertKpiStrip        (Critical·High·Unacknowledged·Active·Resolved24h)
│   └── CriticalIncidentQueue(critical/high + active + !acknowledged)
├── FleetAlertIntelligence
│   ├── MostActiveVehicles   (severity-weighted, links to vehicle)
│   └── AlertDistribution    (active-only severity OR category; labeled population)
├── LiveNowBand
│   └── DrivingEventsFeed    (WS, only pulsing surface)
├── AlertHistoryTable
│   ├── AlertTableFilters    (existing AlertFilters)
│   ├── AlertTable           (rows; links + ack/resolve row actions)
│   └── AlertStatusTabs
└── AlertDrawer (command panel)
    ├── AlertDrawerHeader    (vehicle, driver, severity, status, category, time)
    ├── AlertEvidence        (message, condition, typed evidence chips)
    ├── AlertRelated         (incident siblings + vehicle/driver/trip links)
    └── AlertActions         (Ack / Resolve; maintenance CTA)
```

Notes: `AlertCard` demoted to compact-row / drawer-related-list use. `AlertKpiCards` → `AlertKpiStrip` (reconcile + clickable). `AlertSummaryChart` and `AlertTimeline` dropped from the page (timeline logic moves into the drawer).

---

## 17. P0–P6 Frontend Implementation Roadmap

P0 — **KPI reconciliation.** Single canonical selector (active-by-severity) in `utils/alerts.js`; strip + donut + queue derive from it; add `Unacknowledged`; make numbers clickable. *(Fix the Critical 8/6 contradiction first.)*
P1 — **Feed → table.** `AlertHistoryTable` (compact, sorted, filtered, paginated/virtualized), status tabs, row links, row ack/resolve; demote `AlertCard`.
P2 — **IA re-layout.** Command header + connection state; move queue up; add LIVE NOW band; keep distribution/most-affected in a framed intelligence panel; remove standalone timeline from page.
P3 — **Incident grouping (client-side).** Group trip alerts by vehicle+trip+day into incident cards with signal chips (`evidence.event_counts`); drawer shows child conditions. No contract change.
P4 — **Staleness + live-vs-historical.** Age thresholds, STALE micro-badge, pulse allowed only in LIVE NOW; connection indicator; stale excluded from strip.
P5 — **Drawer command panel.** Four-zone layout, evidence chips, related alerts, vehicle/driver/trip links, maintenance CTA → Maintenance page.
P6 — **Polish & verification.** Empty/stale/offline states, zero-slice handling, category "Unclassified" label, final lint/build/test pass.

## 18. Definition of Done

- **Reconciliation rule:** every KPI/chart on the page derives from one canonical population; a re-render produces identical sums to the DB query (spot-check section 4 table).
- **No-fabrication rule:** no timestamp, telemetry, severity, or message invented on the client; NULL fields render as muted "—/Unclassified", never invented.
- **Live/historical rule:** no element older than 24 h uses a live pulse or top-strip placement.
- **Connectivity rule:** page states websocket state; feed updates are applied only from verified `alert_event` messages.
- **Verification:** `npx vitest run` green (existing 52 + new), `npx eslint src` introduces zero new errors (6 pre-existing baseline documented), `npm run build` passes; a `git status` diff limited to the listed files.
- **Review:** user sign-off on the rendered page at 61-row dataset.

## 19. Files Likely to Change

- `frontend/src/utils/alerts.js` — canonical selectors, KPI semantics, grouping helpers
- `frontend/src/hooks/useAlerts.js` — expose unacknowledged/stale/grouped derivations
- `frontend/src/pages/Alerts.jsx` — new IA layout
- `frontend/src/components/alerts/AlertKpiCards.jsx` → strip (reconcile + links)
- `frontend/src/components/alerts/AlertSummaryChart.jsx` — labeled population, zero-slice handling
- `frontend/src/components/alerts/AlertDistribution.jsx` — "Unclassified" label
- `frontend/src/components/alerts/CriticalIncidentQueue.jsx` — reposition, exclude stale
- `frontend/src/components/alerts/LiveAlertFeed.jsx` → `AlertHistoryTable` (or renamed component)
- `frontend/src/components/alerts/AlertDrawer.jsx` — command panel refactor
- `frontend/src/components/alerts/AlertTimeline.jsx` — removed from page (logic → drawer)
- `frontend/src/components/alerts/MostActiveVehicles.jsx` — severity-weighted ranking
- New: `CommandHeader`, `LiveNowBand`, `AlertHistoryTable`, `AlertStatusTabs`
- Tests: `frontend/src/services/alertAdapter.test.js` + new `utils/alerts` tests (grouping, staleness, reconciliation)

## 20. Risks / Dependencies

- **Backfill dependency (P2 backend):** 32 legacy NULL-category rows remain "Unclassified" until a migration backfills `category`/`condition`/`message`; the frontend cannot invent them. Do not ship the distribution section claiming real data while 52% are NULL.
- **Incident grouping dependency:** client-side grouping (P3) is an approximation (keyed vehicle+trip+day); a true `incident_id` needs a backend column + engine change. Approx can over-merge if two distinct incidents share a vehicle/trip/day window.
- **Staleness dependency:** the DB holds week-old `active` rows because `resolve_stale` only runs with the engine. Frontend degradation (P4) masks it; a backend sweep is required for correctness.
- **`/alerts/stats` label trap:** backend `critical_active`/`high_active` counts do not filter by status; any future frontend use of `stats()` will reproduce the P-1 contradiction. Fix in Phase 2 before the frontend adopts it.
- **Live events lack timestamps:** `active_event_types` is keyed `vehicle:event_type` with no time, so "LIVE NOW" cannot sort by event time; keep it as a presence feed, not a chronological log.
- **Card-wall legacy:** removing surfaces (timeline, donut) is intentional per the standing rule; ensure no other page imports the removed composition.
- **Test data vs prod:** tests build schema via `Base.metadata.create_all` (not alembic); a migration-based backfill must also be applied to `drivevitals_test` or the 52 test-suite may diverge from `drivevitals_dev`.
- **Non-risks:** ack/resolve, canonical mapping, websocket wiring, and adapter coverage are already green (backend 225, frontend 52) and are not touched by this roadmap.
