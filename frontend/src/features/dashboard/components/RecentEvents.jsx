import { ListTree } from 'lucide-react';
import Card from '../../../components/common/Card/Card';

// RecentEvents: Sprint 1 empty state. Event feed arrives in a later sprint.
function RecentEvents() {
  return (
    <Card title="Recent Events" className="widget-empty-card">
      <div className="widget-empty-state">
        <ListTree size={22} strokeWidth={1.5} className="widget-empty-icon" />
        <p className="text-caption">No data available</p>
      </div>
    </Card>
  );
}

export default RecentEvents;
