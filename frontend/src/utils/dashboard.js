/**
 * Canonical dashboard selectors.
 *
 * Every number on the Dashboard page derives from the canonical data
 * layer — the merged fleet snapshot (`useVehicles`), the canonical Alerts
 * selectors (`useAlerts` / `useLiveEvents`) and the canonical Maintenance
 * selectors (`useMaintenance`). Nothing here fabricates metrics: unknown
 * values are `null` (rendered as "—"), never zero, and offline data is
 * surfaced as a connection state, never as an all-clear.
 */

import { canonicalHealthCategory } from './health';
import { computeVehicleRisk, isActive } from './alerts';
import {
  computeVehicleMaintenanceRisk,
  formatMaintenanceDue,
  sortMaintenanceWorkItems,
} from './maintenance';

/** A live snapshot with no update within this window is "stale", not "live". */
export const SNAPSHOT_STALE_MS = 60 * 1000;

export const TRIAGE_ORDER = ['critical', 'high', 'medium', 'stale', 'normal'];

export const TRIAGE_META = {
  critical: { label: 'Critical', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  high: { label: 'High', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  medium: { label: 'Medium', color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
  stale: { label: 'No Live Data', color: 'var(--color-text-muted)', bg: 'var(--color-surface-hover)' },
  normal: { label: 'Normal', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
};

/**
 * Mean fleet health over vehicles with a real score. Returns null when no
 * vehicle carries a score — unknown is never rendered as 0.
 */
export function computeFleetHealthAverage(vehicles) {
  const list = Array.isArray(vehicles) ? vehicles : [];
  const scores = list
    .map((v) => v?.healthScore ?? v?.overall_health_score)
    .filter((s) => s != null && Number.isFinite(Number(s)));
  if (scores.length === 0) return null;
  return Math.round(scores.reduce((sum, s) => sum + Number(s), 0) / scores.length);
}

/**
 * Vehicles currently in the ACTIVE display status. Only meaningful while
 * the socket is live; callers must gate this on the connection state.
 */
export function computeActiveNowCount(vehicles) {
  const list = Array.isArray(vehicles) ? vehicles : [];
  return list.filter((v) => v?.displayStatus === 'ACTIVE').length;
}

/**
 * Connection state for the dashboard's own surfaces. A "live" socket whose
 * last snapshot is older than SNAPSHOT_STALE_MS is reported as "stale" so
 * the UI never claims live data it does not have.
 */
export function deriveConnectionState(connectionStatus, lastUpdate, now = Date.now()) {
  if (connectionStatus === 'live') {
    const last = lastUpdate != null ? new Date(lastUpdate).getTime() : lastUpdate;
    if (typeof last === 'number' && Number.isFinite(last) && now - last > SNAPSHOT_STALE_MS) {
      return 'stale';
    }
  }
  return connectionStatus || 'offline';
}

function healthCategoryFor(v) {
  if (v?.healthCategory) return v.healthCategory;
  return canonicalHealthCategory(v?.healthScore ?? null, v?.healthStatus ?? null);
}

/**
 * Rank vehicles for triage. The level ladder is fixed and documented —
 * it does NOT invent a risk formula, it orders existing canonical signals:
 *
 *   critical  live events, or critical/high active alerts
 *   high      maintenance overdue/due-soon, or critical health
 *   medium    any active alert, health warning, or scheduled maintenance
 *   stale     no live telemetry (displayStatus OFFLINE)
 *   normal    everything else
 *
 * Sorting: level -> severity-weighted alert risk desc -> live events desc
 * -> health score asc (null last) -> vehicle id.
 */
export function rankVehiclesForTriage(vehicles, { alerts, liveEvents, workItems }) {
  const list = Array.isArray(vehicles) ? vehicles : [];
  const alertList = Array.isArray(alerts) ? alerts : [];
  const eventList = Array.isArray(liveEvents) ? liveEvents : [];
  const itemList = Array.isArray(workItems) ? workItems : [];

  const riskByVehicle = new Map();
  for (const r of computeVehicleRisk(alertList)) {
    riskByVehicle.set(r.vehicle_id, r);
  }

  return list
    .map((v) => {
      const vehicleId = v.id;
      const activeAlerts = alertList.filter((a) => isActive(a) && a.vehicle_id === vehicleId);
      const criticalHigh = activeAlerts.filter(
        (a) => a.severity === 'critical' || a.severity === 'high'
      );
      const events = eventList.filter((e) => e.vehicle_id === vehicleId);
      const items = itemList.filter((w) => w.vehicle_id === vehicleId);
      const overdue = items.filter((w) => w.dueStatus === 'overdue').length;
      const dueSoon = items.filter((w) => w.dueStatus === 'dueSoon').length;
      const scheduled = items.filter((w) => w.dueStatus === 'scheduled').length;
      const healthCategory = healthCategoryFor(v);

      let level = 'normal';
      if (events.length > 0 || criticalHigh.length > 0) level = 'critical';
      else if (overdue > 0 || dueSoon > 0 || healthCategory === 'critical') level = 'high';
      else if (activeAlerts.length > 0 || healthCategory === 'warning' || scheduled > 0) level = 'medium';
      else if (v.displayStatus === 'OFFLINE') level = 'stale';

      const reasons = [];
      if (events.length > 0) {
        reasons.push(`Live: ${events.map((e) => e.label).filter(Boolean).join(', ')}`);
      }
      if (criticalHigh.length > 0) {
        const n = criticalHigh.length;
        reasons.push(`${n} critical/high alert${n === 1 ? '' : 's'}`);
      }
      if (overdue > 0) reasons.push(`${overdue} overdue service${overdue === 1 ? '' : 's'}`);
      if (dueSoon > 0) reasons.push(`${dueSoon} due-soon service${dueSoon === 1 ? '' : 's'}`);
      if (activeAlerts.length > 0) {
        const n = activeAlerts.length;
        reasons.push(`${n} active alert${n === 1 ? '' : 's'}`);
      }
      if (healthCategory === 'critical') reasons.push('Critical health');
      if (healthCategory === 'warning') reasons.push('Health warning');
      if (scheduled > 0) reasons.push(`${scheduled} scheduled service${scheduled === 1 ? '' : 's'}`);
      if (level === 'stale') reasons.push('No live telemetry');

      const risk = riskByVehicle.get(vehicleId);
      return {
        id: vehicleId,
        name: v.name,
        driver: v.driver,
        driverId: v.driverId,
        displayStatus: v.displayStatus,
        healthScore: v.healthScore ?? null,
        healthStatus: v.healthStatus ?? null,
        healthCategory,
        lastUpdate: v.lastUpdate ?? null,
        level,
        reasons,
        riskScore: risk?.riskScore ?? 0,
        activeAlertCount: activeAlerts.length,
        criticalHighAlertCount: criticalHigh.length,
        liveEventCount: events.length,
        maintenanceActionable: overdue + dueSoon + scheduled,
      };
    })
    .sort((a, b) => {
      const levelDiff =
        TRIAGE_ORDER.indexOf(a.level) - TRIAGE_ORDER.indexOf(b.level);
      if (levelDiff !== 0) return levelDiff;
      const riskDiff = b.riskScore - a.riskScore;
      if (riskDiff !== 0) return riskDiff;
      const eventsDiff = b.liveEventCount - a.liveEventCount;
      if (eventsDiff !== 0) return eventsDiff;
      const ah = a.healthScore == null ? Infinity : a.healthScore;
      const bh = b.healthScore == null ? Infinity : b.healthScore;
      if (ah !== bh) return ah - bh;
      return String(a.id).localeCompare(String(b.id));
    });
}

/** Attention summary over ranked rows, excluding `normal`. */
export function summarizeAttention(rows) {
  const list = Array.isArray(rows) ? rows : [];
  const counts = { critical: 0, high: 0, medium: 0, stale: 0 };
  for (const r of list) {
    if (r.level !== 'normal' && r.level in counts) counts[r.level] += 1;
  }
  counts.total = counts.critical + counts.high + counts.medium + counts.stale;
  return counts;
}

/**
 * Vehicles with actionable maintenance (overdue / due-soon / scheduled),
 * joined to the nearest work item for a due label. Derives entirely from
 * the canonical work items — no estimated service history.
 */
export function buildMaintenancePressureRows(workItems, fleetMeta) {
  const itemList = Array.isArray(workItems) ? workItems : [];
  const riskRows = computeVehicleMaintenanceRisk(itemList, fleetMeta);
  return riskRows
    .filter((r) => r.actionable > 0)
    .map((r) => {
      const nearest = sortMaintenanceWorkItems(
        itemList.filter((w) => w.vehicle_id === r.vehicle_id),
        'status'
      )[0];
      return {
        ...r,
        dueLabel: nearest ? formatMaintenanceDue(nearest) : null,
        serviceLabel: nearest ? nearest.maintenanceTypeLabel : null,
      };
    });
}

/**
 * Data-quality gate for driver ranking. Driver safety scores come from
 * backend driver statistics; when none exist, or the best score is
 * implausibly low (a collection/calibration signal), ranking is hidden
 * behind an explicit data-quality state instead of showing garbage.
 */
export function driverRankingQuality(drivers) {
  const list = Array.isArray(drivers) ? drivers : [];
  const scored = list.filter((d) => d?.historical?.safetyScore != null);
  if (scored.length === 0) return 'no-data';
  const maxScore = Math.max(...scored.map((d) => d.historical.safetyScore));
  if (maxScore < 10) return 'degraded';
  return 'ok';
}
