/**
 * Pure presentational helpers for the Alerts page.
 *
 * These helpers NEVER generate alerts, incidents, driving events,
 * timestamps, telemetry or health scores. Every value they return is
 * derived from backend-provided alert fields (see `alertAdapter.js`).
 *
 * A single set of canonical selectors feeds every surface on the Alerts
 * page (KPI strip, queue, distribution, risk panel, insights, table) so
 * every count reconciles against the same source of truth.
 */

import { severityRank, categoryLabel } from '../services/alertAdapter';

const H_MS = 60 * 60 * 1000;

export const SEVERITY_WEIGHTS = {
  critical: 5,
  high: 4,
  medium: 2,
  low: 1,
  info: 0,
};

/** Active alerts are considered stale after this age and hard-stale beyond. */
export const STALE_AFTER_H = 24;
export const STALE_HARD_H = 72;

export function severityIcon(severity) {
  switch (severity) {
    case 'critical':
    case 'high':
    case 'medium':
      return '\u26A0';
    default:
      return '\u25CF';
  }
}

export function severityColor(severity) {
  switch (severity) {
    case 'critical':
      return 'var(--color-red)';
    case 'high':
      return 'var(--color-amber)';
    case 'medium':
      return 'var(--color-blue)';
    case 'low':
    case 'info':
      return 'var(--color-accent)';
    case 'resolved':
      return 'var(--color-green)';
    default:
      return 'var(--color-text-muted)';
  }
}

export function severityBg(severity) {
  switch (severity) {
    case 'critical':
      return 'var(--color-red-bg)';
    case 'high':
      return 'var(--color-amber-bg)';
    case 'medium':
      return 'var(--color-blue-bg)';
    case 'low':
    case 'info':
      return 'var(--color-accent-subtle)';
    case 'resolved':
      return 'var(--color-green-bg)';
    default:
      return 'var(--color-surface-hover)';
  }
}

export function severityLabel(severity) {
  switch (severity) {
    case 'critical':
      return 'Critical';
    case 'high':
      return 'High';
    case 'medium':
      return 'Medium';
    case 'low':
      return 'Low';
    case 'info':
      return 'Information';
    case 'resolved':
      return 'Resolved';
    default:
      return severity || null;
  }
}

export function isActive(a) {
  return !!a && a.status === 'active';
}

export function isUnacknowledged(a) {
  return isActive(a) && !a.acknowledged;
}

export function isCriticalActive(a) {
  return isActive(a) && a.severity === 'critical';
}

export function isHighActive(a) {
  return isActive(a) && a.severity === 'high';
}

function parseTime(iso) {
  if (!iso) return null;
  const t = new Date(iso).getTime();
  return Number.isNaN(t) ? null : t;
}

export function withinHours(iso, hours, now = Date.now()) {
  const t = parseTime(iso);
  if (t == null) return false;
  return now - t <= hours * H_MS;
}

/**
 * Canonical KPI counts for the KPI strip. Every metric is derived purely
 * from backend alert rows and every surface on the page consumes these:
 *
 * - critical       active alerts with severity critical
 * - high           active alerts with severity high
 * - unacknowledged active alerts not yet acknowledged
 * - active         active alerts
 * - resolved24h    resolved alerts with a resolved_at within the last 24h
 *
 * There is no response-time metric — no fabricated latency values.
 */
export function computeAlertKpis(alerts, now = Date.now()) {
  const list = Array.isArray(alerts) ? alerts : [];
  const active = list.filter(isActive);
  return {
    critical: active.filter((a) => a.severity === 'critical').length,
    high: active.filter((a) => a.severity === 'high').length,
    unacknowledged: active.filter((a) => !a.acknowledged).length,
    active: active.length,
    resolved24h: list.filter((a) => a.status === 'resolved' && withinHours(a.resolved_at, 24, now)).length,
  };
}

/**
 * Severity distribution over ACTIVE alerts only. Slices with a zero count
 * are omitted so the chart never claims data that is not present.
 */
export function computeActiveSeverityDistribution(alerts) {
  const counts = { critical: 0, high: 0, medium: 0, low: 0, info: 0 };
  const list = Array.isArray(alerts) ? alerts : [];
  list.filter(isActive).forEach((a) => {
    if (a.severity in counts) counts[a.severity] += 1;
  });
  return [
    { key: 'critical', label: 'Critical', color: 'var(--color-red)', count: counts.critical },
    { key: 'high', label: 'High', color: 'var(--color-amber)', count: counts.high },
    { key: 'medium', label: 'Medium', color: 'var(--color-blue)', count: counts.medium },
    { key: 'low', label: 'Low', color: 'var(--color-accent)', count: counts.low },
    { key: 'info', label: 'Information', color: 'var(--color-text-muted)', count: counts.info },
  ].filter((s) => s.count > 0);
}

/**
 * Alerts without a backend category are labelled "Unclassified" — never
 * lumped into "Other" — so legacy rows are surfaced honestly.
 */
export function categoryDisplayLabel(category) {
  return categoryLabel(category) || 'Unclassified';
}

/**
 * Category distribution over ACTIVE alerts only. `key` preserves the raw
 * category (null => Unclassified) so clicks can drive the filter.
 */
export function computeActiveCategoryDistribution(alerts) {
  const counts = {};
  const list = Array.isArray(alerts) ? alerts : [];
  const active = list.filter(isActive);
  active.forEach((a) => {
    const label = categoryDisplayLabel(a.category);
    const key = a.category ?? null;
    const bucket = counts[key] || { key, label, count: 0 };
    bucket.count += 1;
    counts[key] = bucket;
  });
  const total = active.length;
  return Object.values(counts)
    .map((entry) => ({
      ...entry,
      pct: total > 0 ? Math.round((entry.count / total) * 100) : 0,
    }))
    .sort((a, b) => b.count - a.count || String(a.label).localeCompare(String(b.label)));
}

/**
 * Severity-weighted active alert load per vehicle. Weighting is fixed
 * (critical 5, high 4, medium 2, low 1, info 0) and disclosed in the UI;
 * it is derived entirely from real alert rows.
 */
export function computeVehicleRisk(alerts) {
  const list = Array.isArray(alerts) ? alerts : [];
  const byVehicle = new Map();
  for (const a of list) {
    if (!isActive(a)) continue;
    if (!byVehicle.has(a.vehicle_id)) {
      byVehicle.set(a.vehicle_id, {
        vehicle_id: a.vehicle_id,
        vehicle_name: a.vehicle_name || a.vehicle_id,
        driver_name: a.driver_name || null,
        activeCount: 0,
        criticalHighCount: 0,
        riskScore: 0,
        categoryCounts: {},
      });
    }
    const v = byVehicle.get(a.vehicle_id);
    v.activeCount += 1;
    v.riskScore += SEVERITY_WEIGHTS[a.severity] ?? 0;
    if (a.severity === 'critical' || a.severity === 'high') v.criticalHighCount += 1;
    const cat = categoryDisplayLabel(a.category);
    v.categoryCounts[cat] = (v.categoryCounts[cat] || 0) + 1;
  }
  return Array.from(byVehicle.values())
    .map((v) => ({
      ...v,
      dominantCategory: Object.entries(v.categoryCounts).sort((x, y) => y[1] - x[1])[0]?.[0] || null,
    }))
    .sort(
      (a, b) =>
        b.riskScore - a.riskScore ||
        b.activeCount - a.activeCount ||
        a.vehicle_id.localeCompare(b.vehicle_id)
    );
}

/**
 * Staleness of an alert, derived from its backend `created_at`. This is a
 * presentational concern only — it never mutates backend state.
 */
export function alertStaleness(a, now = Date.now()) {
  const t = parseTime(a?.created_at);
  if (t == null) return { level: 'unknown', hours: null };
  const hours = (now - t) / H_MS;
  if (hours < STALE_AFTER_H) return { level: 'fresh', hours };
  if (hours < STALE_HARD_H) return { level: 'stale', hours };
  return { level: 'hard-stale', hours };
}

export function isStaleActive(a, now = Date.now()) {
  if (!isActive(a)) return false;
  const s = alertStaleness(a, now);
  return s.level === 'stale' || s.level === 'hard-stale';
}

function titleCase(value) {
  if (!value) return null;
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function aggregateEventCounts(children) {
  const out = {};
  for (const c of children) {
    const ec = c.evidence?.event_counts;
    if (!ec || typeof ec !== 'object') continue;
    for (const [k, v] of Object.entries(ec)) {
      if (typeof v === 'number') out[k] = (out[k] || 0) + v;
    }
  }
  return out;
}

/**
 * Group alerts into incidents. Alerts that share a backend `trip_id` are
 * one incident (the trip fan-out signals); alerts without a trip id stay
 * independent. Severity/status/category of the incident follow the most
 * severe child. Sorting is severity desc, then newest created first.
 */
export function groupAlertsIntoIncidents(alerts) {
  const list = Array.isArray(alerts) ? alerts : [];
  const groups = new Map();
  for (const a of list) {
    const key = a.trip_id ? `trip:${a.trip_id}` : `alert:${a.alert_id}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(a);
  }

  const incidents = [];
  for (const [key, children] of groups) {
    let max = children[0];
    let maxRank = severityRank(max.severity);
    for (const a of children) {
      const r = severityRank(a.severity);
      if (r < maxRank) {
        maxRank = r;
        max = a;
      }
    }
    const head = children[0];
    const createdTimes = children.map((c) => parseTime(c.created_at)).filter((t) => t != null);
    const resolvedTimes = children.map((c) => parseTime(c.resolved_at)).filter((t) => t != null);
    const anyActive = children.some(isActive);
    const allAcknowledged = children.every((c) => c.acknowledged);

    incidents.push({
      key,
      id: key,
      alert_ids: children.map((c) => c.alert_id),
      children,
      groupCount: children.length,
      vehicle_id: head.vehicle_id,
      vehicle_name: head.vehicle_name || head.vehicle_id,
      driver_id: head.driver_id ?? null,
      driver_name: head.driver_name || null,
      trip_id: head.trip_id ?? null,
      condition: max.condition,
      alert_type: max.alert_type,
      title: titleCase(max.condition) || titleCase(max.alert_type) || 'Alert',
      message: max.message,
      category: max.category,
      category_label: categoryDisplayLabel(max.category),
      severity: max.severity,
      status: anyActive ? 'active' : 'resolved',
      acknowledged: allAcknowledged,
      created_at: createdTimes.length ? new Date(Math.min(...createdTimes)).toISOString() : null,
      resolved_at: resolvedTimes.length ? new Date(Math.max(...resolvedTimes)).toISOString() : null,
      eventCounts: aggregateEventCounts(children),
    });
  }

  return incidents.sort((a, b) => {
    const r = severityRank(a.severity) - severityRank(b.severity);
    if (r !== 0) return r;
    return (parseTime(b.created_at) || 0) - (parseTime(a.created_at) || 0);
  });
}

const EVENT_COUNT_LABELS = {
  total: 'events',
  overspeeding: 'overspeed',
  harsh_braking: 'braking',
  harsh_acceleration: 'acceleration',
  severe: 'severe',
};

export const EVENT_COUNT_ORDER = [
  'total',
  'overspeeding',
  'harsh_braking',
  'harsh_acceleration',
  'severe',
];

/**
 * Compact human summary of an incident's aggregated event counts,
 * e.g. "134 events · 54 severe". Returns null when no counts exist.
 */
export function formatEventCounts(eventCounts) {
  if (!eventCounts || typeof eventCounts !== 'object') return null;
  const parts = EVENT_COUNT_ORDER.filter((k) => eventCounts[k] > 0).map((k) => {
    const label = EVENT_COUNT_LABELS[k] || k.replace(/_/g, ' ');
    return `${eventCounts[k]} ${label}`;
  });
  return parts.length ? parts.join(' · ') : null;
}

/**
 * Operational insights derived only from real data. Each callout is
 * emitted only when its backing fact is present.
 */
export function computeInsights(alerts, now = Date.now()) {
  const list = Array.isArray(alerts) ? alerts : [];
  const insights = [];
  const active = list.filter(isActive);
  const criticalActive = active.filter((a) => a.severity === 'critical').length;
  const unacknowledged = active.filter((a) => !a.acknowledged).length;
  const unclassified = active.filter((a) => a.category == null).length;
  const stale = active.filter((a) => isStaleActive(a, now)).length;

  if (criticalActive > 0) {
    insights.push({
      kind: 'ATTENTION',
      text: `${criticalActive} critical alert${criticalActive === 1 ? '' : 's'} ${criticalActive === 1 ? 'requires' : 'require'} attention.`,
    });
  }
  if (unacknowledged > 0) {
    insights.push({
      kind: 'ATTENTION',
      text: `${unacknowledged} active alert${unacknowledged === 1 ? '' : 's'} ${unacknowledged === 1 ? 'is' : 'are'} unacknowledged.`,
    });
  }
  const risk = computeVehicleRisk(list);
  const top = risk[0];
  if (top && top.activeCount >= 2) {
    insights.push({
      kind: 'RISK',
      text: `${top.vehicle_name} has the highest active incident load (${top.activeCount} active, risk ${top.riskScore}).`,
    });
  }
  const catDist = computeActiveCategoryDistribution(list);
  const dominant = catDist[0];
  if (dominant && dominant.count >= 2 && active.length > 0) {
    insights.push({
      kind: 'INSIGHT',
      text: `${dominant.label} is the dominant active-alert category (${dominant.count} of ${active.length}).`,
    });
  }
  if (top && active.length >= 4 && top.activeCount / active.length >= 0.5) {
    insights.push({
      kind: 'INSIGHT',
      text: `Active alerts are concentrated in ${top.vehicle_name} (${top.activeCount} of ${active.length}).`,
    });
  }
  if (stale > 0) {
    insights.push({
      kind: 'STALE',
      text: `${stale} active alert${stale === 1 ? '' : 's'} ${stale === 1 ? 'is' : 'are'} stale (>${STALE_AFTER_H}h old).`,
    });
  }
  if (unclassified > 0) {
    insights.push({
      kind: 'DATA QUALITY',
      text: `${unclassified} active alert${unclassified === 1 ? '' : 's'} ${unclassified === 1 ? 'is' : 'are'} unclassified.`,
    });
  }
  return insights;
}

/**
 * Real calendar time-range filtering over `created_at`.
 *
 * - 'live'  -> only active alerts (current state, not a time window)
 * - '1h'    -> created within the last hour
 * - 'today' -> created on the same calendar day (local)
 * - '7d' / '30d' -> created within the last N days
 * - 'all'   -> everything
 *
 * Alerts with no created_at are never matched by a time window; only
 * 'live' and 'all' include them.
 */
export function inTimeRange(alert, range, now = Date.now()) {
  if (!alert) return false;
  if (range === 'live') return alert.status === 'active';
  if (range === 'all') return true;

  const created = alert.created_at ? new Date(alert.created_at).getTime() : null;
  if (created == null || Number.isNaN(created)) {
    return range === 'live' || range === 'all';
  }

  if (range === '1h') return now - created <= 60 * 60 * 1000;
  if (range === 'today') {
    const then = new Date(created);
    const nowD = new Date(now);
    return (
      then.getFullYear() === nowD.getFullYear() &&
      then.getMonth() === nowD.getMonth() &&
      then.getDate() === nowD.getDate()
    );
  }
  if (range === '7d') return now - created <= 7 * 24 * 60 * 60 * 1000;
  if (range === '30d') return now - created <= 30 * 24 * 60 * 60 * 1000;
  return false;
}

export function filterAlertsByTimeRange(alerts, range, now = Date.now()) {
  const list = Array.isArray(alerts) ? alerts : [];
  return list.filter((a) => inTimeRange(a, range, now));
}

export const CATEGORIES = [
  'safety_driving',
  'vehicle_health',
  'cooling',
  'fuel',
  'engine',
  'electrical',
  'transmission',
  'brakes',
  'maintenance',
  'trip',
  'other',
];

export const SEVERITIES = ['all', 'critical', 'high', 'medium', 'low', 'info'];
export const TIME_RANGES = ['live', '1h', 'today', '7d', '30d', 'all'];
