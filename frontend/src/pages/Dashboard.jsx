import { WifiOff } from 'lucide-react';
import { DashboardCommandHeader } from '../components/dashboard/DashboardCommandHeader';
import { AttentionRequired } from '../components/dashboard/AttentionRequired';
import { DashboardKpiStrip } from '../components/dashboard/DashboardKpiStrip';
import { LiveFleetTable } from '../components/dashboard/LiveFleetTable';
import { TopRiskVehicles } from '../components/dashboard/TopRiskVehicles';
import { MaintenancePressure } from '../components/dashboard/MaintenancePressure';
import { DriverInsights } from '../components/dashboard/DriverInsights';
import { useDashboard } from '../hooks/useDashboard';

export function Dashboard() {
  const { connState } = useDashboard();
  const dataLimited = connState === 'offline' || connState === 'stale';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 1400 }}>
      <DashboardCommandHeader />

      {dataLimited && (
        <div
          className="fade-in"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 16px',
            borderRadius: 12,
            background: 'var(--color-amber-bg)',
            border: '1px solid var(--color-amber)',
            fontSize: 12,
            fontWeight: 500,
            color: 'var(--color-text-primary)',
          }}
        >
          <WifiOff size={14} style={{ color: 'var(--color-amber)', flexShrink: 0 }} />
          <span>
            Live data {connState === 'stale' ? 'is stale' : 'is unavailable'} — showing the last known state of the fleet.
          </span>
        </div>
      )}

      <AttentionRequired />

      <DashboardKpiStrip />

      <LiveFleetTable />

      <div className="two-col-grid">
        <TopRiskVehicles />
        <MaintenancePressure />
      </div>

      <DriverInsights />
    </div>
  );
}
