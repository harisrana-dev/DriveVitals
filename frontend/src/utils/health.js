export const HEALTHY_MIN = 90;
export const WARNING_MIN = 70;

export const HEALTH_SEVERITY_COLORS = {
  critical: 'var(--color-red)',
  warning: 'var(--color-amber)',
  info: 'var(--color-blue)',
};

export const HEALTH_SEVERITY_BG = {
  critical: 'var(--color-red-bg)',
  warning: 'var(--color-amber-bg)',
  info: 'var(--color-blue-bg)',
};

export const HEALTH_SEVERITY_LABEL = {
  critical: 'Critical',
  warning: 'Warning',
  info: 'Info',
};

export function canonicalHealthCategory(score, status) {
  if (status === 'healthy' || status === 'warning' || status === 'critical') {
    return status;
  }
  if (score == null) return 'unavailable';
  if (score >= HEALTHY_MIN) return 'healthy';
  if (score >= WARNING_MIN) return 'warning';
  return 'critical';
}

export function healthCategory(score) {
  return canonicalHealthCategory(score, null);
}

export function healthLabel(category) {
  switch (category) {
    case 'healthy': return 'Healthy';
    case 'warning': return 'Warning';
    case 'critical': return 'Critical';
    case 'unavailable': return 'Unavailable';
    default: return category || 'Unavailable';
  }
}

export function healthColor(categoryOrScore) {
  const category =
    typeof categoryOrScore === 'number' || categoryOrScore == null
      ? canonicalHealthCategory(categoryOrScore, null)
      : categoryOrScore;
  switch (category) {
    case 'healthy': return 'var(--color-green)';
    case 'warning': return 'var(--color-amber)';
    case 'critical': return 'var(--color-red)';
    default: return 'var(--color-text-muted)';
  }
}

export function healthBg(categoryOrScore) {
  const category =
    typeof categoryOrScore === 'number' || categoryOrScore == null
      ? canonicalHealthCategory(categoryOrScore, null)
      : categoryOrScore;
  switch (category) {
    case 'healthy': return 'var(--color-green-bg)';
    case 'warning': return 'var(--color-amber-bg)';
    case 'critical': return 'var(--color-red-bg)';
    default: return 'var(--color-surface-hover)';
  }
}

export function componentLabel(key) {
  switch (key) {
    case 'engine': return 'Engine';
    case 'cooling': return 'Cooling';
    case 'braking': return 'Brakes';
    case 'transmission': return 'Transmission';
    case 'fuel': return 'Fuel System';
    default: return key;
  }
}

export function healthReasonLabel(reason) {
  if (!reason) return 'Health concern detected';
  const idx = String(reason).indexOf(' (');
  const head = idx >= 0 ? String(reason).slice(0, idx) : String(reason);
  const detail = idx >= 0 ? String(reason).slice(idx) : '';
  return head.charAt(0).toUpperCase() + head.slice(1) + detail;
}

export const SUBSYSTEM_ORDER = ['engine', 'cooling', 'brakes', 'transmission', 'fuel_system'];

export const SUBSYSTEM_LABELS = {
  engine: 'Engine',
  cooling: 'Cooling',
  brakes: 'Brakes',
  transmission: 'Transmission',
  fuel_system: 'Fuel System',
};

export function subsystemLabel(subsystem) {
  return SUBSYSTEM_LABELS[subsystem] || subsystem || 'Health';
}

// Subsystem -> maintenance types that would address the concern.
export const SUBSYSTEM_MAINTENANCE_TYPES = {
  engine: ['oil_change', 'general_inspection'],
  cooling: ['coolant', 'general_inspection'],
  brakes: ['brake_inspection', 'general_inspection'],
  transmission: ['general_inspection'],
  fuel_system: ['general_inspection'],
};

/**
 * Safely extract a string value from any input.
 * Never produces '[object Object]' — prefers known text fields on objects,
 * falls back to empty string for null/undefined/objects without text fields.
 */
function extractString(value, fallback) {
  if (typeof value === 'string') return value;
  if (value == null) return fallback || '';
  if (typeof value === 'object' && !Array.isArray(value)) {
    for (const key of ['message', 'title', 'text', 'description', 'summary', 'label']) {
      if (typeof value[key] === 'string') return value[key];
    }
    return fallback || '';
  }
  return fallback || '';
}

/**
 * Normalize the health_reasons stream (structured { subsystem, reason }
 * entries, matching the WebSocket and REST payloads) into a stable,
 * deduplicated, subsystem-ordered list with all fields guaranteed to be
 * safe primitives — never raw objects.
 */
export function normalizeHealthReasons(reasons) {
  const raw = Array.isArray(reasons) ? reasons : [];
  const normalized = [];
  const seen = new Set();

  for (const entry of raw) {
    if (!entry) continue;

    const isString = typeof entry === 'string';
    const subsystem = isString ? '' : extractString(entry.subsystem, '');
    const reasonText = isString ? entry : extractString(entry.reason, '');
    if (!reasonText) continue;

    const key = `${subsystem}\u0000${reasonText}`;
    if (seen.has(key)) continue;
    seen.add(key);

    const sev = extractString(entry.severity, 'warning');
    const severity = sev === 'critical' ? 'critical' : sev === 'info' ? 'info' : 'warning';

    normalized.push({
      subsystem,
      reason: reasonText,
      code: extractString(entry.code, ''),
      title: extractString(entry.title, '') || reasonText,
      severity,
      summary: extractString(entry.summary, '') || reasonText,
      evidence: entry.evidence && typeof entry.evidence === 'object' && !Array.isArray(entry.evidence) ? entry.evidence : null,
      impact: extractString(entry.impact, ''),
      recommendation: extractString(entry.recommendation, ''),
    });
  }

  normalized.sort((a, b) => {
    const ia = SUBSYSTEM_ORDER.indexOf(a.subsystem);
    const ib = SUBSYSTEM_ORDER.indexOf(b.subsystem);
    const ra = ia === -1 ? SUBSYSTEM_ORDER.length : ia;
    const rb = ib === -1 ? SUBSYSTEM_ORDER.length : ib;
    return ra - rb;
  });

  return normalized;
}

export function topHealthReason(reasons) {
  const normalized = normalizeHealthReasons(reasons);
  return normalized[0] || null;
}

const REASON_THRESHOLDS = [
  {
    match: 'rpm above redline',
    configKey: 'engine',
    key: 'redline_rpm',
    labelFor: (v) => `redline limit ${Math.round(v).toLocaleString()} rpm`,
  },
  {
    match: 'sustained high rpm',
    configKey: 'engine',
    key: 'sustained_rpm',
    labelFor: (v) => `normal below ${Math.round(v).toLocaleString()} rpm`,
  },
  {
    match: 'engine overheating',
    configKey: 'engine',
    key: 'overheat_temp_c',
    labelFor: (v) => `overheating at ${Math.round(v)} \u00B0C`,
  },
  {
    match: 'sustained high engine load',
    configKey: 'engine',
    key: 'max_load_percent',
    labelFor: (v) => `sustained load limit ${Math.round(v)}%`,
  },
  {
    match: 'excessive throttle abuse',
    configKey: 'engine',
    key: 'throttle_abuse_percent',
    labelFor: (v) => `throttle abuse above ${Math.round(v)}%`,
  },
  {
    match: 'aggressive throttle events',
    configKey: 'engine',
    key: 'aggressive_throttle_event_cap',
    labelFor: (v) => `capped at ${Math.round(v)} events`,
  },
  {
    match: 'overheating',
    configKey: 'cooling',
    key: 'overheat_temp_c',
    labelFor: (v) => `overheating at ${Math.round(v)} \u00B0C`,
  },
  {
    match: 'elevated coolant temperature',
    configKey: 'cooling',
    key: 'elevated_temp_c',
    labelFor: (v) => `elevated above ${Math.round(v)} \u00B0C`,
  },
  {
    match: 'unstable coolant temperature',
    configKey: 'cooling',
    key: 'stability_stddev_c',
    labelFor: (v) => `stable within ${v.toFixed(1)} \u00B0C`,
  },
  {
    match: 'high thermal load',
    configKey: 'cooling',
    key: 'max_load_percent',
    labelFor: (v) => `thermal load limit ${Math.round(v)}%`,
  },
  {
    match: 'harsh braking pressure',
    configKey: 'brake',
    key: 'harsh_brake_pressure',
    labelFor: (v) => `harsh braking above ${Math.round(v * 100)}%`,
  },
  {
    match: 'frequent hard braking',
    configKey: 'brake',
    key: 'hard_brake_fraction',
    labelFor: (v) => `normal within ${Math.round(v * 100)}% of window`,
  },
  {
    match: 'high rpm at low speed',
    configKey: 'transmission',
    key: 'stress_rpm',
    labelFor: (v) => `stress above ${Math.round(v).toLocaleString()} rpm`,
  },
  {
    match: 'repeated drivetrain stress',
    configKey: 'transmission',
    key: 'stress_fraction',
    labelFor: (v) => `normal within ${Math.round(v * 100)}% of window`,
  },
  {
    match: 'poor fuel efficiency',
    configKey: 'fuel_system',
    key: 'min_efficiency_km_per_l',
    labelFor: (v) => `minimum ${v.toFixed(1)} km/L`,
  },
  {
    match: 'excessive fuel consumption',
    configKey: 'fuel_system',
    key: 'high_consumption_fraction',
    labelFor: (v) => `normal within ${Math.round(v * 100)}% of window`,
  },
  {
    match: 'high throttle fuel use',
    configKey: 'fuel_system',
    key: 'abuse_throttle_percent',
    labelFor: (v) => `throttle above ${Math.round(v)}%`,
  },
];

/**
 * Contextual label for a single health reason, derived from the canonical
 * health thresholds served by the /vehicle-health/config endpoint.
 * Returns null when no threshold applies or the config is unavailable.
 */
export function reasonThresholdLabel(reason, healthConfig) {
  if (!reason || !reason.reason) return null;
  const text = reason.reason;
  for (const descriptor of REASON_THRESHOLDS) {
    if (text.includes(descriptor.match)) {
      const thresholds = healthConfig?.[descriptor.configKey];
      const value = thresholds?.[descriptor.key];
      if (value == null) return null;
      return descriptor.labelFor(value);
    }
  }
  return null;
}
