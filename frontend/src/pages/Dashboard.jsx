import { DashboardCommandHeader } from '../components/dashboard/DashboardCommandHeader';
import { AttentionRequired } from '../components/dashboard/AttentionRequired';
import { DashboardKpiStrip } from '../components/dashboard/DashboardKpiStrip';
import { LiveFleetTable } from '../components/dashboard/LiveFleetTable';
import { TopRiskVehicles } from '../components/dashboard/TopRiskVehicles';
import { MaintenancePressure } from '../components/dashboard/MaintenancePressure';
import { DriverInsights } from '../components/dashboard/DriverInsights';

export function Dashboard() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 1400 }}>
      <DashboardCommandHeader />

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
