import { FleetPulse } from '../components/dashboard/FleetPulse';
import { KpiCards } from '../components/dashboard/KpiCards';
import { AttentionRequired } from '../components/dashboard/AttentionRequired';
import { LiveFleetActivity } from '../components/dashboard/LiveFleetActivity';
import { FleetHealthMatrix } from '../components/dashboard/FleetHealthMatrix';
import { DriverInsights } from '../components/dashboard/DriverInsights';
import { MaintenanceQueue } from '../components/dashboard/MaintenanceQueue';
import { FleetTrends } from '../components/dashboard/FleetTrends';

export function Dashboard() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 1400 }}>
      {/* Dashboard Header */}
      <div className="fade-in" style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        marginBottom: 4,
      }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Dashboard
          </h1>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
            Real-time fleet intelligence and operational insights
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <KpiCards />

      {/* Fleet Pulse */}
      <FleetPulse />

      {/* Two-column: Attention + Health Matrix */}
      <div className="two-col-grid">
        <AttentionRequired />
        <FleetHealthMatrix />
      </div>

      {/* Live Fleet Activity */}
      <LiveFleetActivity />

      {/* Fleet Trends */}
      <FleetTrends />

      {/* Two-column: Drivers + Maintenance */}
      <div className="two-col-grid">
        <DriverInsights />
        <MaintenanceQueue />
      </div>
    </div>
  );
}
