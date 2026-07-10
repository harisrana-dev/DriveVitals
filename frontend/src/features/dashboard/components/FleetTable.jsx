import { Search, SlidersHorizontal, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import Card from '../../../components/common/Card/Card';
import { statusColorMap, statusLabelMap } from '../dashboardData';
import { useDashboard } from '../../../context/DashboardContext';

const COLUMNS = [
  { key: 'vehicle', label: 'Vehicle' },
  { key: 'driver', label: 'Driver' },
  { key: 'status', label: 'Status' },
  { key: 'speed', label: 'Speed' },
  { key: 'consumption', label: 'Consumption' },
  { key: 'health', label: 'Health' },
  { key: 'driverScore', label: 'Driver Score' },
  { key: 'alerts', label: 'Alerts' },
  { key: 'lastUpdated', label: 'Last Updated' },
];

// FleetTable: the primary operational surface of the dashboard.
// Sprint 1: mock data, sticky header, and inert search/filter/sort/pagination
// affordances. Later sprints will swap fleetTableData for live WebSocket rows.
function FleetTable() {

  const { vehicles } = useDashboard();

  const rows = Object.values(vehicles).map((vehicle) => {

  console.log("Vehicle:", vehicle);

  return {

    id: vehicle.vehicle_id,

    vehicle: vehicle.vehicle_id,

    driver: vehicle.telemetry.driver_id,

    status: vehicle.status,

    speed: `${vehicle.telemetry.speed_kmh} km/h`,

    consumption: `${vehicle.telemetry.fuel_rate_lph.toFixed(2)} L/h`,

    health: vehicle.vehicle_health.health,

    driverScore: "--",

    alerts: vehicle.alerts.length,

    lastUpdated: new Date(vehicle.last_updated).toLocaleTimeString(),

  };

});
  return (
    <Card
      title="Live Fleet"
      className="fleet-table-card"
      noPadding
      action={
        <div className="fleet-table-toolbar">
          <div className="fleet-table-search">
            <Search size={14} strokeWidth={2} />
            <input type="text" placeholder="Search fleet…" disabled />
          </div>
          <button type="button" className="fleet-table-toolbar-btn" disabled>
            <SlidersHorizontal size={14} strokeWidth={2} />
            Filter
          </button>
        </div>
      }
    >
      <div className="fleet-table-scroll">
        <table className="fleet-table">
          <thead>
            <tr>
              {COLUMNS.map((col) => (
                <th key={col.key}>
                  <button type="button" className="fleet-table-sort-btn" disabled>
                    <span>{col.label}</span>
                    <ArrowUpDown size={12} strokeWidth={2} />
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row)=>(
              <tr key={row.id} className="fleet-table-row">
                <td className="fleet-table-vehicle-cell">{row.vehicle}</td>
                <td>{row.driver}</td>
                <td>
                  <span className={`status-badge status-badge--${statusColorMap[row.status]}`}>
                    {statusLabelMap[row.status]}
                  </span>
                </td>
                <td>{row.speed}</td>
                <td>{row.consumption}</td>
                <td>

                <span
                className={`status-badge status-badge--${row.health}`}
                >

                {row.health}

                </span>

                </td>
                <td>{row.driverScore}</td>
                <td>
                  {row.alerts > 0 ? (
                    <span className="status-badge status-badge--critical">{row.alerts}</span>
                  ) : (
                    <span className="text-caption">—</span>
                  )}
                </td>
                <td className="text-caption">{row.lastUpdated}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="fleet-table-pagination">
        <span className="text-caption">Showing 1–4 of 44 vehicles</span>
        <div className="fleet-table-pagination-controls">
          <button type="button" className="fleet-table-page-btn" disabled>
            <ChevronLeft size={14} strokeWidth={2} />
          </button>
          <span className="text-caption">Page 1 of 8</span>
          <button type="button" className="fleet-table-page-btn" disabled>
            <ChevronRight size={14} strokeWidth={2} />
          </button>
        </div>
      </div>
    </Card>
  );
}

export default FleetTable;
