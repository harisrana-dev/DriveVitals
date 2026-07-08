import KPICard from './KPICard';
import { kpiData } from '../dashboardData';

// KPIGrid: exactly six KPI cards, per Sprint 1 spec.
function KPIGrid() {
  return (
    <section className="kpi-grid" aria-label="Fleet key performance indicators">
      {kpiData.map((kpi) => (
        <KPICard key={kpi.id} {...kpi} />
      ))}
    </section>
  );
}

export default KPIGrid;
