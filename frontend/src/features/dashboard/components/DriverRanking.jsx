import { Users } from 'lucide-react';
import Card from '../../../components/common/Card/Card';
import { useDashboard } from "../../../context/dashboardContext";


// DriverRanking: Displays live driver safety rankings
function DriverRanking() {

    const { vehicles } = useDashboard();


    const fleet = Object.values(vehicles);

    console.log("Fleet:", fleet);


    const rankings = fleet
        .filter(vehicle => vehicle.driver_ranking)
        .map(vehicle => ({
            driverId: vehicle.driver_ranking.driver_id,
            vehicleId: vehicle.driver_ranking.vehicle_id,
            score: vehicle.driver_ranking.score,
            grade: vehicle.driver_ranking.grade,
        }));


    rankings.sort((a, b) => b.score - a.score);


    console.log("Rankings:", rankings);



    return (

        <Card title="Top Drivers" className="widget-empty-card">


            {rankings.length === 0 ? (

                <div className="widget-empty-state">

                    <Users
                        size={22}
                        strokeWidth={1.5}
                        className="widget-empty-icon"
                    />

                    <p className="text-caption">
                        No data available
                    </p>

                </div>


            ) : (


                <table className="driver-ranking-table">


                    <thead>

                        <tr>

                            <th>Rank</th>
                            <th>Driver</th>
                            <th>Vehicle</th>
                            <th>Score</th>
                            <th>Grade</th>

                        </tr>

                    </thead>



                    <tbody>


                        {rankings.map((driver, index) => (


                            <tr key={driver.driverId}>


                                {/* Rank */}

                                <td>

                                    <span className="driver-rank">

                                        #{index + 1}


                                        {
                                            driver.score < 75 && (

                                                <span className="warning-icon">
                                                    ⚠
                                                </span>

                                            )
                                        }

                                    </span>

                                </td>



                                {/* Driver */}

                                <td>

                                    <div className="driver-info">

                                        <Users size={15} />

                                        <span>
                                            {driver.driverId}
                                        </span>

                                    </div>

                                </td>



                                {/* Vehicle */}

                                <td>

                                    <span className="vehicle-badge">

                                        {driver.vehicleId}

                                    </span>

                                </td>




                                {/* Score */}

                                <td>


                                    <div className="score-wrapper">


                                        <div className="score-number">

                                            {driver.score}

                                            <span>
                                                /100
                                            </span>

                                        </div>



                                        <div className="score-bar">


                                            <div

                                                className="score-fill"

                                                style={{
                                                    width: `${driver.score}%`
                                                }}

                                            >

                                            </div>


                                        </div>


                                    </div>


                                </td>





                                {/* Grade */}

                                <td>


                                    <span

                                        className={
                                            `grade-badge ${
                                                driver.grade
                                                    .toLowerCase()
                                                    .replace(" ", "-")
                                            }`
                                        }

                                    >

                                        {driver.grade}


                                    </span>


                                </td>



                            </tr>


                        ))}



                    </tbody>


                </table>


            )}


        </Card>

    );

}


export default DriverRanking;