import Card from '../../../components/common/Card/Card';
import { useDashboard } from "../../../context/DashboardContext";

// FleetHealth: fleet-wide status breakdown strip.
// Sprint 1 restriction: no gauges, no charts — plain counts + status badges only.


function FleetHealth() {
    const { vehicles } = useDashboard();

    const fleet = Object.values(vehicles);

    const healthyCount = fleet.filter(
       vehicle => vehicle.vehicle_health.health === "healthy"
    ).length;

    const warningCount = fleet.filter(
      vehicle => vehicle.alerts.length > 0
    ).length;

    const criticalCount = fleet.filter(
      vehicle => vehicle.alerts.some(
        alert => alert.severity === "CRITICAL"
      )
    ).length;

    const maintenanceCount = fleet.filter(
      vehicle => vehicle.vehicle_health.health === "maintenance"
    ).length;

    const offlineCount = 0;

    const STATUS_BREAKDOWN = [
  {
    key: "healthy",
    label: "Healthy",
    count: healthyCount,
    color: "var(--color-status-healthy)",
  },
  {
    key: "warning",
    label: "Warning",
    count: warningCount,
    color: "var(--color-status-warning)",
  },
  {
    key: "critical",
    label: "Critical",
    count: criticalCount,
    color: "var(--color-status-critical)",
  },
  {
    key: "maintenance",
    label: "In Maintenance",
    count: maintenanceCount,
    color: "var(--color-status-maintenance)",
  },
  {
    key: "offline",
    label: "Offline",
    count: offlineCount,
    color: "var(--color-status-offline)",
  },
];
  return (
    <Card title="Fleet Health Overview" className="fleet-health">
      <div className="fleet-health-breakdown">
        {STATUS_BREAKDOWN.map(({ key, label, count, color }) => (
          <div key={key} className="fleet-health-item">
            <span className="fleet-health-dot" style={{ backgroundColor: color }} />
            <span className="fleet-health-count">{count}</span>
            <span className="fleet-health-label text-caption">{label}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default FleetHealth;
