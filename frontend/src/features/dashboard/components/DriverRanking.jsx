import { Users } from 'lucide-react';
import Card from '../../../components/common/Card/Card';

// DriverRanking: Sprint 1 empty state. Ranking logic arrives in a later sprint.
function DriverRanking() {
  return (
    <Card title="Top Drivers" className="widget-empty-card">
      <div className="widget-empty-state">
        <Users size={22} strokeWidth={1.5} className="widget-empty-icon" />
        <p className="text-caption">No data available</p>
      </div>
    </Card>
  );
}

export default DriverRanking;
