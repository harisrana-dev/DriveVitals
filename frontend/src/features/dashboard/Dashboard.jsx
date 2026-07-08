import KPIGrid from './components/KPIGrid';
import FleetHealth from './components/FleetHealth';
import FleetTable from './components/FleetTable';
import DriverRanking from './components/DriverRanking';
import MaintenanceQueue from './components/MaintenanceQueue';
import FleetTrends from './components/FleetTrends';
import RecentEvents from './components/RecentEvents';
import './Dashboard.css';

// Dashboard: Sprint 1 — layout skeleton only.
// No charts, gauges, WebSocket, or API calls. Static/mock data throughout.
function Dashboard() {
  return (
    <div className="dashboard">
      <div className="dashboard-heading">
        <h1 className="text-dashboard-title">Fleet Command Center</h1>
        <p className="text-caption">Overview of fleet health, activity, and operations</p>
      </div>

      <KPIGrid />

      <FleetHealth />

      <section className="dashboard-section">
        <FleetTable />
      </section>

      <section className="dashboard-section dashboard-widgets-row">
        <DriverRanking />
        <MaintenanceQueue />
      </section>

      <section className="dashboard-section dashboard-widgets-row">
        <FleetTrends />
        <RecentEvents />
      </section>
    </div>
  );
}

export default Dashboard;
