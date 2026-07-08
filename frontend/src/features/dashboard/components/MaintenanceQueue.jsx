import { Wrench } from 'lucide-react';
import Card from '../../../components/common/Card/Card';

// MaintenanceQueue: Sprint 1 empty state. Queue logic arrives in a later sprint.
function MaintenanceQueue() {
  return (
    <Card title="Maintenance Queue" className="widget-empty-card">
      <div className="widget-empty-state">
        <Wrench size={22} strokeWidth={1.5} className="widget-empty-icon" />
        <p className="text-caption">No data available</p>
      </div>
    </Card>
  );
}

export default MaintenanceQueue;
