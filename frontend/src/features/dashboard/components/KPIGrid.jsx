import KPICard from './KPICard';
import { useDashboard } from '../../../context/DashboardContext';
import {
  Truck,
  MapPin,
  Fuel,
  DollarSign,
  Wrench,
  UserCheck,
} from 'lucide-react';

function KPIGrid() {
  const { vehicles } = useDashboard();
  const fleet = Object.values(vehicles);

  /* ── Derived metrics ─────────────────────────────────── */

  // 🚚 Total Vehicles
  const totalVehicles = fleet.length;

  // 📍 Total Distance Travelled (sum of odometer readings, km)
  const totalDistance = fleet
    .reduce((sum, v) => sum + (v.telemetry?.odometer_km ?? 0), 0)
    .toLocaleString();

  // ⛽ Fuel Consumed (sum across fleet, litres)
  const fuelConsumed = fleet
    .reduce((sum, v) => sum + (v.fuel_efficiency?.total_fuel_consumed_liters ?? 0), 0)
    .toLocaleString();

  // 💰 Fleet Operating Cost (sum of trip costs)
  const operatingCost = fleet
    .reduce((sum, v) => sum + (v.financials?.operating_cost_usd ?? 0), 0)
    .toLocaleString();

  // 🔧 Maintenance Due
  const maintenanceDue = fleet.filter(
    (v) =>
      v.alerts?.some((a) => a.type === 'maintenance') ||
      v.vehicle_health?.health === 'maintenance'
  ).length;

  // 👨‍✈️ Active Drivers
  const activeDrivers = fleet.filter(
    (v) => v.status === 'active' || v.telemetry?.speed_kmh > 0
  ).length;

  /* ── Statuses ─────────────────────────────────────────── */
  const maintenanceStatus = maintenanceDue === 0 ? 'healthy' : maintenanceDue >= 5 ? 'critical' : 'warning';
  const driverStatus      = activeDrivers === 0  ? 'offline' : 'healthy';

  const kpiData = [
    {
      id:         'total-vehicles',
      icon:       Truck,
      title:      'Total Vehicles',
      value:      totalVehicles || '--',
      context:    'Fleet Size',
      statusText: totalVehicles > 0 ? 'Registered' : 'No data',
      status:     'healthy',          // 🟢 Green
    },
    {
      id:         'total-distance',
      icon:       MapPin,
      title:      'Total Distance',
      value:      totalDistance ? `${totalDistance} km` : '--',
      context:    'Odometer Sum',
      statusText: 'All Vehicles',
      status:     'info',             // 🔵 Blue
    },
    {
      id:         'fuel-consumed',
      icon:       Fuel,
      title:      'Fuel Consumed',
      value:      fuelConsumed ? `${fuelConsumed} L` : '--',
      context:    'Fleet Total',
      statusText: 'This Period',
      status:     'warning',          // 🟠 Orange
    },
    {
      id:         'operating-cost',
      icon:       DollarSign,
      title:      'Fleet Operating Cost',
      value:      operatingCost ? `$${operatingCost}` : '--',
      context:    'Total Spend',
      statusText: 'This Period',
      status:     'info',             // 🔵 Blue
    },
    {
      id:         'maintenance-due',
      icon:       Wrench,
      title:      'Maintenance Due',
      value:      maintenanceDue,
      context:    'Vehicles',
      statusText: maintenanceDue === 0 ? 'All Clear' : 'Requires Action',
      status:     maintenanceStatus,  // 🟢 / 🟠 / 🔴 based on count
    },
    {
      id:         'active-drivers',
      icon:       UserCheck,
      title:      'Active Drivers',
      value:      activeDrivers || '--',
      context:    'On Duty Now',
      statusText: activeDrivers > 0 ? 'Live' : 'None On Duty',
      status:     driverStatus,       // 🟢 Green
    },
  ];

  return (
    <section className="kpi-grid" aria-label="Fleet key performance indicators">
      {kpiData.map((kpi) => (
        <KPICard key={kpi.id} {...kpi} />
      ))}
    </section>
  );
}

export default KPIGrid;
