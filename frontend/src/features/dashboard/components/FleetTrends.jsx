import { LineChart } from 'lucide-react';
import Card from '../../../components/common/Card/Card';

// FleetTrends: Sprint 1 empty state. Charts (Recharts) arrive in a later sprint.
function FleetTrends() {
  return (
    <Card title="Fleet Trends" className="widget-empty-card">
      <div className="widget-empty-state">
        <LineChart size={22} strokeWidth={1.5} className="widget-empty-icon" />
        <p className="text-caption">No data available</p>
      </div>
    </Card>
  );
}

export default FleetTrends;
