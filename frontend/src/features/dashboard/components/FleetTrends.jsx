
import {
    ResponsiveContainer,
    LineChart,
    Line,
    CartesianGrid,
    XAxis,
    YAxis,
    Tooltip
} from "recharts";

import Card from "../../../components/common/Card/Card";
import { useDashboard } from "../../../context/DashboardContext";

// FleetTrends: Sprint 1 empty state. Charts (Recharts) arrive in a later sprint.
function FleetTrends() {
    const { fleetTrends } = useDashboard();
    console.log("Fleet Trends Component:", fleetTrends);
    const CustomTooltip = ({ active, payload, label }) => {

    if (!active || !payload || !payload.length) {
        return null;
    }

    return (
        <div className="chart-tooltip">

            <p>{label}</p>

            <strong>
                {payload[0].value} km/L
            </strong>

        </div>
    );
};
  return (
    <Card title="Fleet Performance Trend">

    {fleetTrends.length === 0 ? (

        <div className="widget-empty-state">

            <p className="text-caption">
                Collecting fleet performance data
            </p>

            <span>
                Waiting for vehicle telemetry...
            </span>

        </div>

    ) : (

        <ResponsiveContainer
            width="100%"
            height={260}
        >

            <LineChart data={fleetTrends}>

                <CartesianGrid
                   stroke="#eef2f7"
                   strokeDasharray="3 3"
                />

                <XAxis
                   dataKey="time"
                   tickLine={false}
                   axisLine={false}
                />

                <YAxis
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value)=>`${value} km/L`}
                />

                <Tooltip content={<CustomTooltip />} />

                <Line
                    type="monotone"
                    dataKey="fuel_efficiency"
                    stroke="#2563eb"
                    strokeWidth={3}
                    dot={false}
                    activeDot={{
                        r:6
                    }}
                    isAnimationActive={true}
                    animationDuration={700}
                />

                <LineChart
                    data={fleetTrends}
                    margin={{
                    top:10,
                    right:20,
                    left:10,
                    bottom:10
                }}
                ></LineChart>

            </LineChart>

        </ResponsiveContainer>

    )}

</Card>
  );
}

export default FleetTrends;
