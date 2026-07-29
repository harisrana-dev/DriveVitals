const SERVICE_INTERVALS = [
  { type: 'Oil Change', intervalKm: 5000, icon: 'oil' },
  { type: 'Brake Inspection', intervalKm: 10000, icon: 'brake' },
  { type: 'Tyre Rotation', intervalKm: 8000, icon: 'tyre' },
  { type: 'Coolant', intervalKm: 20000, icon: 'coolant' },
  { type: 'General Inspection', intervalKm: 15000, icon: 'general' },
];

const SERVICE_ICONS = {
  oil: '\u26EF',
  brake: '\u26FD',
  tyre: '\u2B24',
  coolant: '\u2744',
  general: '\u2699',
};

export function serviceIcon(type) {
  const entry = SERVICE_INTERVALS.find((s) => s.type === type);
  return entry ? SERVICE_ICONS[entry.icon] : '\u25CF';
}

export function priorityForHealth(score) {
  if (score < 50) return 'critical';
  if (score < 80) return 'due';
  return 'good';
}

export function dueStatus(remainingKm) {
  if (remainingKm <= 0) return 'OVERDUE';
  if (remainingKm <= 500) return 'DUE SOON';
  if (remainingKm <= 2000) return 'SCHEDULED';
  return 'GOOD';
}

export function dueStatusStyle(status) {
  switch (status) {
    case 'OVERDUE': return { color: 'var(--color-red)', bg: 'var(--color-red-bg)' };
    case 'DUE SOON': return { color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' };
    case 'SCHEDULED': return { color: 'var(--color-accent)', bg: 'var(--color-accent-subtle)' };
    case 'GOOD': return { color: 'var(--color-green)', bg: 'var(--color-green-bg)' };
    default: return { color: 'var(--color-text-muted)', bg: 'var(--color-surface-hover)' };
  }
}

export function priorityStyle(priority) {
  switch (priority) {
    case 'critical': return { color: 'var(--color-red)', bg: 'var(--color-red-bg)' };
    case 'due': return { color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' };
    case 'good': return { color: 'var(--color-green)', bg: 'var(--color-green-bg)' };
    default: return { color: 'var(--color-text-muted)', bg: 'var(--color-surface-hover)' };
  }
}

export function computeNextService(vehicle) {
  const odometer = vehicle.odometer_km ?? 0;
  const health = vehicle.overall_health_score ?? 100;

  const services = SERVICE_INTERVALS.map((svc) => {
    const cyclesSince = Math.floor(odometer / svc.intervalKm);
    const doneAt = cyclesSince * svc.intervalKm;
    const dueKm = doneAt + svc.intervalKm;
    const remainingKm = Math.max(0, dueKm - odometer);
    return { ...svc, dueKm, remainingKm, doneAt };
  });

  const healthPenalty = health < 50 ? 3000 : health < 80 ? 1000 : 0;
  services.sort((a, b) => (a.remainingKm - healthPenalty) - (b.remainingKm - healthPenalty));

  const next = services[0];
  const adjustedRemaining = Math.max(0, next.remainingKm - healthPenalty);

  return {
    serviceType: next.type,
    dueKm: next.dueKm,
    remainingKm: adjustedRemaining,
    dueStatus: dueStatus(adjustedRemaining),
    priority: priorityForHealth(health),
    overdue: adjustedRemaining <= 0,
  };
}

export function buildServiceQueue(vehicles) {
  if (!vehicles || vehicles.length === 0) return [];
  return vehicles
    .map((v) => {
      const svc = computeNextService(v);
      return {
        id: v.vehicle_id,
        vehicleId: v.vehicle_id,
        vehicleName: v.vehicle_name || v.vehicle_id,
        driverName: v.driver_name || '\u2014',
        priority: svc.priority,
        serviceType: svc.serviceType,
        dueKm: svc.dueKm,
        remainingKm: svc.remainingKm,
        dueStatus: svc.dueStatus,
        health: v.overall_health_score ?? 100,
        odometer: v.odometer_km ?? 0,
        status: svc.dueStatus,
        overdue: svc.overdue,
      };
    })
    .sort((a, b) => {
      const order = { critical: 0, due: 1, good: 2 };
      return order[a.priority] - order[b.priority] || a.remainingKm - b.remainingKm;
    });
}

export function buildDistribution(vehicles) {
  if (!vehicles || vehicles.length === 0) return [];
  const counts = {};
  vehicles.forEach((v) => {
    const svc = computeNextService(v);
    counts[svc.serviceType] = (counts[svc.serviceType] || 0) + 1;
  });
  return SERVICE_INTERVALS.map((s) => ({
    label: s.type,
    count: counts[s.type] || 0,
  }));
}

export function buildKpiStats(vehicles) {
  if (!vehicles || vehicles.length === 0) {
    return { requiresService: 0, overdue: 0, upcoming: 0, compliancePct: 0, total: 0 };
  }
  const total = vehicles.length;
  let requiresService = 0;
  let overdue = 0;
  let upcoming = 0;
  let compliant = 0;

  vehicles.forEach((v) => {
    const svc = computeNextService(v);
    if (svc.overdue || v.overall_health_score < 80) requiresService++;
    if (svc.overdue) overdue++;
    if (svc.remainingKm <= 2000 && !svc.overdue) upcoming++;
    if (v.overall_health_score >= 80) compliant++;
  });

  return {
    requiresService,
    overdue,
    upcoming,
    compliancePct: total > 0 ? Math.round((compliant / total) * 100) : 0,
    total,
  };
}

export function buildUpcomingSchedule(vehicles) {
  if (!vehicles || vehicles.length === 0) return [];
  const now = Date.now();
  const day = 86400000;

  const groups = [
    { label: 'Today', range: [0, 1], items: [] },
    { label: 'This Week', range: [1, 7], items: [] },
    { label: 'Next Week', range: [7, 14], items: [] },
    { label: 'Next Month', range: [14, 30], items: [] },
  ];

  vehicles.forEach((v) => {
    const svc = computeNextService(v);
    if (svc.dueStatus === 'GOOD') return;
    const daysUntilDue = svc.overdue ? 0 : Math.round(svc.remainingKm / 500);
    const groupIdx = groups.findIndex((g) => daysUntilDue >= g.range[0] && daysUntilDue < g.range[1]);
    if (groupIdx >= 0) {
      groups[groupIdx].items.push({
        vehicleId: v.vehicle_id,
        vehicleName: v.vehicle_name || v.vehicle_id,
        serviceType: svc.serviceType,
        daysUntilDue,
        priority: svc.priority,
      });
    }
  });

  return groups.filter((g) => g.items.length > 0);
}

export function estimateFleetCost(vehicles) {
  if (!vehicles || vehicles.length === 0) {
    return { monthly: 0, upcoming: 0, critical: 0 };
  }
  const avgCostPerService = 180;
  const criticalCost = 350;
  let monthlyCount = 0;
  let criticalCount = 0;
  let upcomingCount = 0;

  vehicles.forEach((v) => {
    const svc = computeNextService(v);
    if (svc.remainingKm <= 2000) monthlyCount++;
    if (svc.overdue) criticalCount++;
    if (svc.remainingKm > 2000 && svc.remainingKm <= 5000) upcomingCount++;
  });

  return {
    monthly: monthlyCount * avgCostPerService,
    upcoming: upcomingCount * avgCostPerService,
    critical: criticalCount * criticalCost,
  };
}

export function buildServiceHistory(vehicles) {
  if (!vehicles || vehicles.length === 0) return [];
  const history = [];
  const serviceNames = ['Oil Change', 'Brake Inspection', 'Tyre Rotation', 'Coolant', 'General Inspection'];

  vehicles.forEach((v) => {
    const odometer = v.odometer_km ?? 0;
    const intervals = [5000, 10000, 8000, 20000, 15000];
    const numServices = Math.min(3, Math.floor(odometer / 5000));

    for (let i = 0; i < numServices; i++) {
      const svcName = serviceNames[i % serviceNames.length];
      const doneKm = Math.max(0, odometer - (i + 1) * 4000 - Math.round(Math.random() * 1000));
      const daysAgo = (i + 1) * 45 + Math.round(Math.random() * 20);
      const d = new Date(Date.now() - daysAgo * 86400000);
      const cost = svcName === 'Oil Change' ? 120 : svcName === 'Brake Inspection' ? 200 : 150;
      history.push({
        id: `${v.vehicle_id}-hist-${i}`,
        vehicleId: v.vehicle_id,
        vehicleName: v.vehicle_name || v.vehicle_id,
        serviceType: svcName,
        date: d.toISOString().split('T')[0],
        mileage: Math.round(doneKm),
        cost: cost + Math.round(Math.random() * 40),
        technician: 'Auto-assigned',
      });
    }
  });

  history.sort((a, b) => new Date(b.date) - new Date(a.date));
  return history.slice(0, 20);
}

export function buildDrawerData(vehicle) {
  const svc = computeNextService(vehicle);
  const health = vehicle.overall_health_score ?? 100;
  const outstanding = svc.dueStatus !== 'GOOD' ? [svc] : [];
  const upcomingServices = [];
  SERVICE_INTERVALS.forEach((s) => {
    const cyclesSince = Math.floor((vehicle.odometer_km ?? 0) / s.intervalKm);
    const doneAt = cyclesSince * s.intervalKm;
    const dueKm = doneAt + s.intervalKm;
    const remainingKm = Math.max(0, dueKm - (vehicle.odometer_km ?? 0));
    if (remainingKm > 0 && s.type !== svc.serviceType) {
      upcomingServices.push({ type: s.type, dueKm, remainingKm });
    }
  });
  upcomingServices.sort((a, b) => a.remainingKm - b.remainingKm);

  const recommendations = [
    {
      component: 'Oil',
      status: svc.serviceType === 'Oil Change' ? svc.overdue ? 'overdue' : 'due' : 'ok',
      recommendation: svc.serviceType === 'Oil Change' ? 'Replace engine oil and filter' : 'Condition satisfactory',
      remainingKm: svc.serviceType === 'Oil Change' ? svc.remainingKm : Math.max(0, 5000 - ((vehicle.odometer_km ?? 0) % 5000)),
    },
    {
      component: 'Brake',
      status: svc.serviceType === 'Brake Inspection' ? svc.overdue ? 'overdue' : 'due' : 'ok',
      recommendation: svc.serviceType === 'Brake Inspection' ? 'Inspect brake pads and rotors' : 'Brake system normal',
      remainingKm: svc.serviceType === 'Brake Inspection' ? svc.remainingKm : Math.max(0, 10000 - ((vehicle.odometer_km ?? 0) % 10000)),
    },
    {
      component: 'Tyres',
      status: svc.serviceType === 'Tyre Rotation' ? svc.overdue ? 'overdue' : 'due' : 'ok',
      recommendation: svc.serviceType === 'Tyre Rotation' ? 'Rotate tyres and check pressure' : 'Tyre condition normal',
      remainingKm: svc.serviceType === 'Tyre Rotation' ? svc.remainingKm : Math.max(0, 8000 - ((vehicle.odometer_km ?? 0) % 8000)),
    },
    {
      component: 'Coolant',
      status: svc.serviceType === 'Coolant' ? svc.overdue ? 'overdue' : 'due' : 'ok',
      recommendation: svc.serviceType === 'Coolant' ? 'Flush and replace coolant' : 'Coolant level adequate',
      remainingKm: svc.serviceType === 'Coolant' ? svc.remainingKm : Math.max(0, 20000 - ((vehicle.odometer_km ?? 0) % 20000)),
    },
    {
      component: 'Battery',
      status: 'ok',
      recommendation: 'Battery charge normal. No service required.',
      remainingKm: 5000 - Math.round(Math.random() * 3000),
    },
  ];

  const history = [];
  const numHistory = Math.min(4, Math.floor((vehicle.odometer_km ?? 0) / 5000));
  const serviceNames = ['Oil Change', 'Brake Inspection', 'Tyre Rotation', 'Coolant', 'General Inspection'];
  for (let i = 0; i < numHistory; i++) {
    const svcName = serviceNames[i % serviceNames.length];
    const doneKm = Math.max(0, (vehicle.odometer_km ?? 0) - (i + 1) * 4000);
    const daysAgo = (i + 1) * 50;
    const d = new Date(Date.now() - daysAgo * 86400000);
    history.push({
      serviceType: svcName,
      date: d.toISOString().split('T')[0],
      mileage: Math.round(doneKm),
    });
  }

  return {
    outstanding,
    upcomingServices,
    recommendations,
    history,
    health,
    odometer: vehicle.odometer_km ?? 0,
    fuelLevel: vehicle.fuel_level_percent ?? 0,
    coolantTemp: vehicle.coolant_temperature_c ?? 0,
  };
}
