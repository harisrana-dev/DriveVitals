import { Wrench } from "lucide-react";
import Card from "../../../components/common/Card/Card";
import { useDashboard } from "../../../context/DashboardContext";

function MaintenanceQueue() {

    const { vehicles } = useDashboard();

    // ----------------------------------
    // Flatten maintenance from all vehicles
    // ----------------------------------

    const maintenance = Object.values(vehicles)
        .flatMap(vehicle => vehicle.maintenance_queue || []);

    // ----------------------------------
    // Sort by priority
    // ----------------------------------

    const priorityOrder = {
        High: 0,
        Medium: 1,
        Low: 2,
    };

    maintenance.sort(
        (a, b) =>
            priorityOrder[a.priority] -
            priorityOrder[b.priority]
    );

    return (

        <Card
            title="Maintenance Queue"
            className="widget-empty-card"
        >

            {maintenance.length === 0 ? (

                <div className="widget-empty-state">

                    <Wrench
                        size={22}
                        strokeWidth={1.5}
                        className="widget-empty-icon"
                    />

                    <p className="text-caption">

                        All fleet vehicles are healthy

                    </p>

                </div>

            ) : (

                <table className="maintenance-table">

                    <thead>

                        <tr>

                            <th>Priority</th>

                            <th>Vehicle</th>

                            <th>Maintenance</th>

                            <th>Due</th>

                        </tr>

                    </thead>

                    <tbody>

                        {maintenance.map((item, index) => (

                            <tr key={index}>

                                <td>

                                    <span
                                        className={`priority-badge priority-${item.priority.toLowerCase()}`}
                                    >

                                        {item.priority}

                                    </span>

                                </td>

                                <td>

                                    {item.vehicle_id}

                                </td>

                                <td>

                                    {item.maintenance}

                                </td>

                                <td>

                                    {item.remaining}

                                </td>

                            </tr>

                        ))}

                    </tbody>

                </table>

            )}

        </Card>

    );

}

export default MaintenanceQueue;