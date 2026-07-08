import { ListTree } from 'lucide-react';
import Card from '../../../components/common/Card/Card';
import { useDashboard } from "../../../context/DashboardContext";

// RecentEvents: Sprint 1 empty state. Event feed arrives in a later sprint.
function RecentEvents() {
    const { vehicles } = useDashboard();

    const fleet = Object.values(vehicles);

    const events = fleet.flatMap(vehicle =>
        vehicle.alerts.map(alert => ({
            ...alert,
            driver_id: vehicle.telemetry.driver_id,
        }))
    );
    console.log(events);
  return (
    <Card title="Recent Events" className="widget-empty-card">
      <div className="widget-empty-state">
        <ListTree size={22} strokeWidth={1.5} className="widget-empty-icon" />
        {events.length === 0 ? (
    <p className="text-caption">No recent events</p>
    ) : (
        events.map((event,index)=>(
           <div key={index}>
               {event.type}
           </div>
        ))
    )}
      </div>
    </Card>
  );
}

export default RecentEvents;
