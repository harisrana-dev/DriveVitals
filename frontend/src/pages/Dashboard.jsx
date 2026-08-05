import { FleetPulse } from '../components/dashboard/FleetPulse';
import { KpiCards } from '../components/dashboard/KpiCards';
import { AttentionRequired } from '../components/dashboard/AttentionRequired';
import { LiveFleetActivity } from '../components/dashboard/LiveFleetActivity';
import { FleetHealthMatrix } from '../components/dashboard/FleetHealthMatrix';
import { DriverInsights } from '../components/dashboard/DriverInsights';
import { MaintenanceQueue } from '../components/dashboard/MaintenanceQueue';
import { FleetTrends } from '../components/dashboard/FleetTrends';
import { ConnectionBadge } from '../components/ui/ConnectionBadge';
import { OfflineState } from '../components/ui/OfflineState';
import { useLiveData } from '../context/LiveDataContext';

export function Dashboard() {
  const { overallStatus } = useLiveData();

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
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <ConnectionBadge status={overallStatus} />
          {overallStatus === 'live' && (
            <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
              Updated just now
            </span>
          )}
          {overallStatus === 'rest' && (
            <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
              Showing REST data
            </span>
          )}
        </div>
      </div>

      {overallStatus === 'offline' ? (
        <OfflineState />
      ) : (
        <>
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
        </>
      )}
    </div>
  );
}
