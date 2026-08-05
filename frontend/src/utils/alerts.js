const DRIVING_EVENT_TYPES = {
  harsh_braking: { label: 'Harsh Braking', icon: 'brake' },
  aggressive_throttle: { label: 'Aggressive Throttle', icon: 'throttle' },
  high_rpm: { label: 'High RPM', icon: 'rpm' },
  speeding: { label: 'Speeding', icon: 'speed' },
};

export function deriveIncidents(vehicles) {
  if (!vehicles || !Array.isArray(vehicles)) return [];

  const incidents = [];

  vehicles.forEach((v) => {
    const vid = v.vehicle_id;
    const vname = v.vehicle_name || vid;
    const dname = v.driver_name || '\u2014';
    const health = v.overall_health_score ?? 100;
    const coolant = v.coolant_temperature_c ?? 0;
    const engineLoad = v.engine_load_percent ?? 0;
    const fuel = v.fuel_level_percent ?? 100;

    if (coolant > 105) {
      incidents.push({
        id: `inc-${vid}-engine-overheat`,
        alert_id: `INC-${vid}-OVH`,
        vehicle_id: vid,
        vehicle_name: vname,
        driver_name: dname,
        event_type: 'engine_overheat',
        eventType: 'Engine Overheat',
        severity: 'critical',
        category: 'Cooling',
        status: 'active',
        description: `Coolant temperature ${coolant.toFixed(1)}°C — exceeds safe threshold`,
        coolant_temperature_c: coolant,
        overall_health_score: health,
        speed: v.speed_kmh ?? 0,
        rpm: v.rpm ?? 0,
        throttle_position_percent: v.throttle_position_percent ?? 0,
        brake_pressure: v.brake_pressure ?? 0,
        engine_load_percent: engineLoad,
        fuel_level_percent: fuel,
      });
    }

    if (fuel < 15) {
      incidents.push({
        id: `inc-${vid}-fuel-critical`,
        alert_id: `INC-${vid}-FUEL`,
        vehicle_id: vid,
        vehicle_name: vname,
        driver_name: dname,
        event_type: 'fuel_critical',
        eventType: 'Fuel Critical',
        severity: 'critical',
        category: 'Fuel',
        status: 'active',
        description: `Fuel level critically low at ${fuel.toFixed(0)}%`,
        fuel_level_percent: fuel,
        overall_health_score: health,
        speed: v.speed_kmh ?? 0,
        rpm: v.rpm ?? 0,
        throttle_position_percent: v.throttle_position_percent ?? 0,
        brake_pressure: v.brake_pressure ?? 0,
        engine_load_percent: engineLoad,
        coolant_temperature_c: coolant,
      });
    }

    if (fuel < 30 && fuel >= 15) {
      incidents.push({
        id: `inc-${vid}-low-fuel`,
        alert_id: `INC-${vid}-LOW`,
        vehicle_id: vid,
        vehicle_name: vname,
        driver_name: dname,
        event_type: 'low_fuel',
        eventType: 'Low Fuel',
        severity: 'warning',
        category: 'Fuel',
        status: 'active',
        description: `Fuel level low at ${fuel.toFixed(0)}% — schedule refuel`,
        fuel_level_percent: fuel,
        overall_health_score: health,
        speed: v.speed_kmh ?? 0,
        rpm: v.rpm ?? 0,
        throttle_position_percent: v.throttle_position_percent ?? 0,
        brake_pressure: v.brake_pressure ?? 0,
        engine_load_percent: engineLoad,
        coolant_temperature_c: coolant,
      });
    }

    if (health < 40) {
      incidents.push({
        id: `inc-${vid}-health-critical`,
        alert_id: `INC-${vid}-HLT`,
        vehicle_id: vid,
        vehicle_name: vname,
        driver_name: dname,
        event_type: 'health_critical',
        eventType: 'Health Critical',
        severity: 'critical',
        category: 'Electrical',
        status: 'active',
        description: `Vehicle health score ${Math.round(health)}% — requires immediate attention`,
        overall_health_score: health,
        speed: v.speed_kmh ?? 0,
        rpm: v.rpm ?? 0,
        throttle_position_percent: v.throttle_position_percent ?? 0,
        brake_pressure: v.brake_pressure ?? 0,
        engine_load_percent: engineLoad,
        fuel_level_percent: fuel,
        coolant_temperature_c: coolant,
      });
    }

    if (health >= 40 && health < 60) {
      incidents.push({
        id: `inc-${vid}-health-warning`,
        alert_id: `INC-${vid}-WRN`,
        vehicle_id: vid,
        vehicle_name: vname,
        driver_name: dname,
        event_type: 'health_warning',
        eventType: 'Health Warning',
        severity: 'warning',
        category: 'Electrical',
        status: 'active',
        description: `Vehicle health at ${Math.round(health)}% — monitor closely`,
        overall_health_score: health,
        speed: v.speed_kmh ?? 0,
        rpm: v.rpm ?? 0,
        throttle_position_percent: v.throttle_position_percent ?? 0,
        brake_pressure: v.brake_pressure ?? 0,
        engine_load_percent: engineLoad,
        fuel_level_percent: fuel,
        coolant_temperature_c: coolant,
      });
    }

    if (coolant > 95 && coolant <= 105) {
      incidents.push({
        id: `inc-${vid}-coolant-warning`,
        alert_id: `INC-${vid}-CLT`,
        vehicle_id: vid,
        vehicle_name: vname,
        driver_name: dname,
        event_type: 'coolant_warning',
        eventType: 'Coolant Warning',
        severity: 'warning',
        category: 'Cooling',
        status: 'active',
        description: `Coolant temperature elevated at ${coolant.toFixed(1)}°C`,
        coolant_temperature_c: coolant,
        overall_health_score: health,
        speed: v.speed_kmh ?? 0,
        rpm: v.rpm ?? 0,
        throttle_position_percent: v.throttle_position_percent ?? 0,
        brake_pressure: v.brake_pressure ?? 0,
        engine_load_percent: engineLoad,
        fuel_level_percent: fuel,
      });
    }

    if (engineLoad > 85) {
      incidents.push({
        id: `inc-${vid}-high-load`,
        alert_id: `INC-${vid}-LOD`,
        vehicle_id: vid,
        vehicle_name: vname,
        driver_name: dname,
        event_type: 'high_engine_load',
        eventType: 'High Engine Load',
        severity: 'warning',
        category: 'Engine',
        status: 'active',
        description: `Engine load at ${engineLoad.toFixed(0)}% — above recommended range`,
        engine_load_percent: engineLoad,
        overall_health_score: health,
        speed: v.speed_kmh ?? 0,
        rpm: v.rpm ?? 0,
        throttle_position_percent: v.throttle_position_percent ?? 0,
        brake_pressure: v.brake_pressure ?? 0,
        fuel_level_percent: fuel,
        coolant_temperature_c: coolant,
      });
    }
  });

  return incidents;
}

export function deriveDrivingEvents(vehicles) {
  if (!vehicles || !Array.isArray(vehicles)) return [];

  const events = [];

  vehicles.forEach((v) => {
    const activeEvents = v.active_event_types || [];

    activeEvents.forEach((evt) => {
      const cfg = DRIVING_EVENT_TYPES[evt];
      if (!cfg) return;
      events.push({
        id: `evt-${v.vehicle_id}-${evt}-${Date.now()}`,
        vehicle_id: v.vehicle_id,
        vehicle_name: v.vehicle_name || v.vehicle_id,
        driver_name: v.driver_name || '\u2014',
        event_type: evt,
        eventType: cfg.label,
        time: new Date().toISOString(),
      });
    });

    if (v.speeding && !activeEvents.includes('speeding')) {
      events.push({
        id: `evt-${v.vehicle_id}-speeding-${Date.now()}`,
        vehicle_id: v.vehicle_id,
        vehicle_name: v.vehicle_name || v.vehicle_id,
        driver_name: v.driver_name || '\u2014',
        event_type: 'speeding',
        eventType: 'Speeding',
        time: new Date().toISOString(),
      });
    }
  });

  events.sort((a, b) => new Date(b.time) - new Date(a.time));
  return events.slice(0, 10);
}

export function severityIcon(severity) {
  switch (severity) {
    case 'critical': return '\u26A0';
    case 'warning': return '\u26A0';
    default: return '\u25CF';
  }
}

export function severityColor(severity) {
  switch (severity) {
    case 'critical': return 'var(--color-red)';
    case 'warning': return 'var(--color-amber)';
    case 'info': return 'var(--color-accent)';
    case 'resolved': return 'var(--color-green)';
    default: return 'var(--color-text-muted)';
  }
}

export function severityBg(severity) {
  switch (severity) {
    case 'critical': return 'var(--color-red-bg)';
    case 'warning': return 'var(--color-amber-bg)';
    case 'info': return 'var(--color-accent-subtle)';
    case 'resolved': return 'var(--color-green-bg)';
    default: return 'var(--color-surface-hover)';
  }
}

export function severityLabel(severity) {
  switch (severity) {
    case 'critical': return 'Critical';
    case 'warning': return 'Warning';
    case 'info': return 'Information';
    case 'resolved': return 'Resolved';
    default: return severity;
  }
}

export function computeAlertKpis(incidents) {
  const critical = incidents.filter((a) => a.severity === 'critical').length;
  const active = incidents.filter((a) => a.status !== 'resolved').length;
  const acknowledged = incidents.filter((a) => a.acknowledged).length;
  const responseTime = 0;
  return { critical, active, acknowledged, responseTime };
}

export function computeSummaryDistribution(incidents) {
  const counts = { critical: 0, warning: 0, info: 0, resolved: 0 };
  incidents.forEach((a) => {
    counts[a.severity] = (counts[a.severity] || 0) + 1;
  });
  return [
    { key: 'critical', label: 'Critical', color: 'var(--color-red)', count: counts.critical },
    { key: 'warning', label: 'Warning', color: 'var(--color-amber)', count: counts.warning },
    { key: 'info', label: 'Information', color: 'var(--color-accent)', count: counts.info },
    { key: 'resolved', label: 'Resolved', color: 'var(--color-green)', count: counts.resolved },
  ];
}

export function computeCategoryDistribution(incidents) {
  const counts = {};
  incidents.forEach((a) => {
    const cat = a.category || 'Other';
    counts[cat] = (counts[cat] || 0) + 1;
  });
  const total = Object.values(counts).reduce((s, c) => s + c, 0);
  return Object.entries(counts).map(([category, count]) => ({
    category,
    count,
    pct: total > 0 ? Math.round((count / total) * 100) : 0,
  })).sort((a, b) => b.count - a.count);
}

export function buildAlertTimeline(incidents) {
  return incidents.map((a) => ({
    id: a.id,
    time: a.started_at || new Date().toISOString(),
    vehicle_name: a.vehicle_name,
    eventType: a.eventType,
    severity: a.severity,
    status: a.status || 'active',
  }));
}

export function buildIncidentTimeline(alert) {
  const base = Date.now();
  return [
    { time: new Date(base - 180000).toISOString(), event: `${alert.eventType} detected` },
    { time: new Date(base - 120000).toISOString(), event: 'Telemetry anomaly confirmed' },
    { time: new Date(base - 60000).toISOString(), event: 'Alert generated' },
    { time: new Date(base).toISOString(), event: 'Awaiting acknowledgment' },
  ];
}

const SUGGESTED_ACTIONS = {
  engine_overheat: 'Reduce engine load immediately. Inspect cooling system. Check coolant level and radiator fan.',
  fuel_critical: 'Refuel at nearest station immediately. Avoid high-load operation.',
  low_fuel: 'Schedule refuel at next available stop.',
  health_critical: 'Vehicle requires immediate inspection. Check all major systems.',
  health_warning: 'Monitor vehicle closely. Schedule diagnostic check.',
  coolant_warning: 'Monitor coolant temperature. Reduce load if temperature rises further.',
  high_engine_load: 'Reduce engine load. Shift to higher gear if possible.',
};

export function getSuggestedAction(alert) {
  return SUGGESTED_ACTIONS[alert.event_type] || 'Monitor vehicle condition. Schedule inspection if needed.';
}

export const CATEGORIES = ['Cooling', 'Fuel', 'Electrical', 'Engine'];
export const SEVERITIES = ['all', 'critical', 'warning'];
export const TIME_RANGES = ['live', '1h', 'today', 'week', 'all'];
