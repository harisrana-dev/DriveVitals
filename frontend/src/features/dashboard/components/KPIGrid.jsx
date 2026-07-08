import KPICard from './KPICard';
import { useDashboard } from '../../../context/DashboardContext';
import {
  Radio,
  HeartPulse,
  TriangleAlert,
  Fuel,
  Gauge,
  Wrench,
} from "lucide-react";

// KPIGrid: exactly six KPI cards, per Sprint 1 spec.
function KPIGrid() {
    const { vehicles } = useDashboard();

    const fleet = Object.values(vehicles);

    const vehiclesOnline = fleet.length;

    const healthyVehicles = fleet.filter(
       vehicle => vehicle.vehicle_health.health === "healthy"
    ).length;

    const activeAlerts = fleet.reduce(
       (total, vehicle) => total + vehicle.alerts.length,
       0
    );

    const averageSpeed =
       fleet.length > 0
          ? (
              fleet.reduce(
                  (total, vehicle) => total + vehicle.telemetry.speed_kmh,
                  0
              ) / fleet.length
          ).toFixed(1)
          : 0;

    const fuelVehicles = fleet.filter(
       vehicle => vehicle.fuel_efficiency.km_per_liter !== null
    );

    const averageFuelEfficiency =
       fuelVehicles.length > 0
          ? (
              fuelVehicles.reduce(
                  (total, vehicle) =>
                      total + vehicle.fuel_efficiency.km_per_liter,
                  0
              ) / fuelVehicles.length
          ).toFixed(1)
          : "--";

   const vehiclesNeedingAttention = fleet.filter(
      vehicle =>
          vehicle.alerts.length > 0 ||
          vehicle.vehicle_health.health !== "healthy"
   ).length;

const kpiData = [
  {
    id: "vehicles-online",
    icon: Radio,
    title: "Vehicles Online",
    value: vehiclesOnline,
    context: "Status",
    statusText: "Live Monitoring",
    status: "info",
  },

  {
    id: "healthy",
    icon: HeartPulse,
    title: "Healthy Vehicles",
    value: healthyVehicles,
    context: "Fleet Health",
    statusText:
      healthyVehicles === vehiclesOnline
        ? "Excellent"
        : "Needs Attention",
    status:
      healthyVehicles === vehiclesOnline
        ? "healthy"
        : "warning",
  },

  {
    id: "alerts",
    icon: TriangleAlert,
    title: "Active Alerts",
    value: activeAlerts,
    context: "Priority",
    statusText:
      activeAlerts > 0
        ? "Needs Review"
        : "No Active Alerts",
    status:
      activeAlerts > 0
        ? "warning"
        : "healthy",
  },

  {
    id: "fuel",
    icon: Fuel,
    title: "Avg Fuel Efficiency",
    value: `${averageFuelEfficiency} km/L`,
    context: "Fleet Average",
    statusText: "Current",
    status: "info",
  },

  {
    id: "speed",
    icon: Gauge,
    title: "Avg Fleet Speed",
    value: `${averageSpeed} km/h`,
    context: "Across Fleet",
    statusText: "Live",
    status: "info",
  },

  {
    id: "attention",
    icon: Wrench,
    title: "Need Attention",
    value: vehiclesNeedingAttention,
    context: "Operations",
    statusText:
      vehiclesNeedingAttention > 0
        ? "Requires Action"
        : "All Clear",
    status:
      vehiclesNeedingAttention > 0
        ? "warning"
        : "healthy",
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
