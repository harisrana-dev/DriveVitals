import { RefreshCw, Radio } from 'lucide-react';
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--color-text-muted)' }}>
            <Radio size={13} style={{ color: 'var(--color-green)' }} />
            <span>Live</span>
          </div>
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            Updated just now
          </span>
          <button
            aria-label="Refresh data"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 32,
              height: 32,
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text-secondary)',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--color-surface-hover)';
              e.currentTarget.style.color = 'var(--color-text-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'var(--color-surface)';
              e.currentTarget.style.color = 'var(--color-text-secondary)';
            }}
          >
            <RefreshCw size={15} strokeWidth={1.8} />
          </button>
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
