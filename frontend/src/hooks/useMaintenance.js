import { useMemo } from 'react';
import { useLiveData } from '../context/LiveDataContext';
import { dueStatus as dueStatusForKm, buildDrawerData } from '../utils/maintenance';

const MAINTENANCE_TYPE_LABELS = {
  oil_change: 'Oil Change',
  brake_inspection: 'Brake Inspection',
  tyre_rotation: 'Tyre Rotation',
  coolant: 'Coolant',
  general_inspection: 'General Inspection',
};

const PRIORITY_ORDER = { critical: 0, due: 1, good: 2 };

function titleCase(value) {
  if (!value) return 'Service';
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function typeLabel(record) {
  return MAINTENANCE_TYPE_LABELS[record.maintenance_type] || titleCase(record.maintenance_type);
}

function remainingFor(record, meta) {
  const odometer = meta?.odometer_km ?? 0;
  const due = record.due_odometer_km;
  if (due == null) return null;
  return Math.max(0, Math.round(due - odometer));
}

function priorityFor(record, remainingKm) {
  const overdue = remainingKm != null && remainingKm === 0;
  if (record.priority === 'critical' || overdue) return 'critical';
  if (record.priority === 'high' || record.priority === 'medium') return 'due';
  return 'good';
}

function mapServiceQueueItem(record, meta) {
  const odometer = meta?.odometer_km ?? 0;
  const due = record.due_odometer_km;
  const remainingKm = remainingFor(record, meta);
  const overdue = remainingKm != null && remainingKm === 0;
  const priority = priorityFor(record, remainingKm);
  const status = remainingKm == null ? 'GOOD' : dueStatusForKm(remainingKm);

  return {
    id: record.maintenance_id,
    vehicleId: record.vehicle_id,
    vehicleName: meta?.vehicle_name || record.vehicle_id,
    driverName: meta?.driver_name || '—',
    priority,
    serviceType: typeLabel(record),
    dueKm: due ?? 0,
    remainingKm: remainingKm ?? 0,
    dueStatus: status,
    health: meta?.overall_health_score ?? 100,
    odometer,
    status,
    overdue,
  };
}

function buildDistribution(records) {
  const counts = {};
  records.forEach((r) => {
    const label = typeLabel(r);
    counts[label] = (counts[label] || 0) + 1;
  });
  return Object.entries(counts)
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count);
}

function buildKpiStats(records, fleetMeta) {
  const total = records.length;
  if (total === 0) {
    return { requiresService: 0, overdue: 0, upcoming: 0, compliancePct: 0, total: 0 };
  }
  let requiresService = 0;
  let overdue = 0;
  let upcoming = 0;

  records.forEach((r) => {
    const remainingKm = remainingFor(r, fleetMeta?.[r.vehicle_id]);
    const priority = priorityFor(r, remainingKm);
    if (priority === 'critical' || (remainingKm != null && remainingKm <= 2000)) requiresService++;
    if (remainingKm != null && remainingKm === 0) overdue++;
    if (remainingKm != null && remainingKm > 0 && remainingKm <= 2000) upcoming++;
  });

  return {
    requiresService,
    overdue,
    upcoming,
    compliancePct: total > 0 ? Math.round(((total - requiresService) / total) * 100) : 0,
    total,
  };
}

function buildUpcomingSchedule(records, fleetMeta) {
  const groups = [
    { label: 'Today', range: [0, 1], items: [] },
    { label: 'This Week', range: [1, 7], items: [] },
    { label: 'Next Week', range: [7, 14], items: [] },
    { label: 'Next Month', range: [14, 30], items: [] },
  ];

  records.forEach((r) => {
    const remainingKm = remainingFor(r, fleetMeta?.[r.vehicle_id]);
    if (remainingKm == null || remainingKm > 5000) return;
    const daysUntilDue = remainingKm === 0 ? 0 : Math.round(remainingKm / 500);
    const groupIdx = groups.findIndex((g) => daysUntilDue >= g.range[0] && daysUntilDue < g.range[1]);
    if (groupIdx >= 0) {
      groups[groupIdx].items.push({
        vehicleId: r.vehicle_id,
        vehicleName: fleetMeta?.[r.vehicle_id]?.vehicle_name || r.vehicle_id,
        serviceType: typeLabel(r),
        daysUntilDue,
        priority: priorityFor(r, remainingKm),
      });
    }
  });

  return groups.filter((g) => g.items.length > 0);
}

function estimateFleetCost(records, fleetMeta) {
  if (!records || records.length === 0) {
    return { monthly: 0, upcoming: 0, critical: 0 };
  }
  const avgCostPerService = 180;
  const criticalCost = 350;
  let monthlyCount = 0;
  let criticalCount = 0;
  let upcomingCount = 0;

  records.forEach((r) => {
    const remainingKm = remainingFor(r, fleetMeta?.[r.vehicle_id]);
    if (remainingKm != null && remainingKm <= 2000) monthlyCount++;
    if (remainingKm != null && remainingKm === 0) criticalCount++;
    if (remainingKm != null && remainingKm > 2000 && remainingKm <= 5000) upcomingCount++;
  });

  return {
    monthly: monthlyCount * avgCostPerService,
    upcoming: upcomingCount * avgCostPerService,
    critical: criticalCount * criticalCost,
  };
}

function buildServiceHistory(records, fleetMeta) {
  if (!Array.isArray(records) || records.length === 0) return [];
  const history = records
    .filter((r) => r.completed_at || r.status === 'completed')
    .map((r) => ({
      id: r.maintenance_id,
      vehicleId: r.vehicle_id,
      vehicleName: fleetMeta?.[r.vehicle_id]?.vehicle_name || r.vehicle_id,
      serviceType: typeLabel(r),
      date: (r.completed_at || r.created_at || '').slice(0, 10),
      mileage: Math.round(r.completed_odometer_km ?? 0),
      cost: 0,
      technician: 'Auto-assigned',
    }));

  history.sort((a, b) => new Date(b.date) - new Date(a.date));
  return history.slice(0, 20);
}

export function useMaintenance() {
  const { maintenance, fleetMeta, mergedFleet } = useLiveData();

  return useMemo(() => {
    if (!Array.isArray(maintenance) || maintenance.length === 0) {
      return {
        serviceQueue: [],
        distribution: [],
        kpiStats: { requiresService: 0, overdue: 0, upcoming: 0, compliancePct: 0, total: 0 },
        upcomingSchedule: [],
        fleetCost: { monthly: 0, upcoming: 0, critical: 0 },
        serviceHistory: [],
        vehicles: mergedFleet,
      };
    }

    const serviceQueue = maintenance
      .map((r) => mapServiceQueueItem(r, fleetMeta?.[r.vehicle_id]))
      .sort(
        (a, b) =>
          PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority] ||
          a.remainingKm - b.remainingKm
      );

    return {
      serviceQueue,
      distribution: buildDistribution(maintenance),
      kpiStats: buildKpiStats(maintenance, fleetMeta),
      upcomingSchedule: buildUpcomingSchedule(maintenance, fleetMeta),
      fleetCost: estimateFleetCost(maintenance, fleetMeta),
      serviceHistory: buildServiceHistory(maintenance, fleetMeta),
      vehicles: mergedFleet,
    };
  }, [maintenance, fleetMeta, mergedFleet]);
}

export function useMaintenanceVehicle(vehicleId) {
  const { mergedFleet } = useLiveData();
  return useMemo(() => {
    if (!Array.isArray(mergedFleet)) return null;
    const vehicle = mergedFleet.find((v) => v.vehicle_id === vehicleId);
    if (!vehicle) return null;
    return { vehicle, drawerData: buildDrawerData(vehicle) };
  }, [mergedFleet, vehicleId]);
}
