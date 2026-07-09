import { ListTree } from 'lucide-react';
import Card from '../../../components/common/Card/Card';
import { useDashboard } from "../../../context/DashboardContext";

function RecentEvents() {

    const { recentEvents } = useDashboard();
    console.log("EVENT DATA:", recentEvents);

    return (
        <Card title="Recent Events" className="widget-empty-card">

            <div className="recent-events-table-wrapper">

                {recentEvents.length === 0 ? (

                    <div className="widget-empty-state">
                        <ListTree
                            size={22}
                            strokeWidth={1.5}
                            className="widget-empty-icon"
                        />

                        <p className="text-caption">
                            No recent events
                        </p>
                    </div>

                ) : (

                    <table className="recent-events-table">

                        <thead>
                            <tr>
                                <th>Fault</th>
                                <th>Vehicle</th>
                                <th>Occurrences</th>
                                <th>Last Seen</th>
                            </tr>
                        </thead>


                        <tbody>

                        {recentEvents.map((event,index)=>(

                        <tr key={index}>

                        <td>

                        <span className="event-name">

                        {event.icon}

                        {event.title}

                        </span>

                        </td>


                        <td>
                        {event.vehicle_id || "Unknown"}
                        </td>


                        <td>
                        x{event.occurrences}
                        </td>

                        
                        <td>
                        {
                         new Date(
                         event.timestamp
                         ).toLocaleTimeString()
                        }
                        </td>
                        


                        </tr>

                        ))}

                        </tbody>

                    </table>

                )}

            </div>

        </Card>
    );
}

export default RecentEvents;