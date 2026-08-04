import { createContext, useContext, useEffect, useState } from "react";
import { subscribeToChannel } from "../websocket";

const LiveDataContext = createContext(null);

export function LiveDataProvider({ children }) {
    const [dashboard, setDashboard] = useState(null);
    const [trips, setTrips] = useState(null);
    const [dashboardConnectionState, setDashboardConnectionState] = useState("connecting");
    const [tripsConnectionState, setTripsConnectionState] = useState("connecting");

    useEffect(() => {
        const unsubscribeDashboard = subscribeToChannel(
            "dashboard",
            {
                onMessage: (message) => {
                    if (
                        message.type === "dashboard_snapshot"
                        && message.data
                    ) {
                        setDashboard(message.data);
                    }
                },
                onState: setDashboardConnectionState,
            }
        );

        const unsubscribeTrips = subscribeToChannel(
            "trips",
            {
                onMessage: (message) => {
                    if (
                        message.type === "trips_snapshot"
                        && message.data
                    ) {
                        setTrips(message.data);
                    }
                },
                onState: setTripsConnectionState,
            }
        );

        return () => {
            unsubscribeDashboard();
            unsubscribeTrips();
        };
    }, []);

    return (
        <LiveDataContext.Provider
            value={{
                dashboard,
                trips,
                dashboardConnectionState,
                tripsConnectionState,
            }}
        >
            {children}
        </LiveDataContext.Provider>
    );
}

export function useLiveData() {
    return useContext(LiveDataContext);
}
