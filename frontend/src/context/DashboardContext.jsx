import { createContext, useContext, useState } from "react";


const DashboardContext = createContext(null);



export function DashboardProvider({ children }) {


    const [vehicles, setVehicles] = useState({});
    const [recentEvents, setRecentEvents] = useState([]);
    const [fleetTrends, setFleetTrends] = useState([]);

    const updateRecentEvents = (events) => {
        setRecentEvents(events);
    };

    const updateVehicle = (vehicle) => {

        setVehicles((previous) => ({

            ...previous,

            [vehicle.vehicle_id]: vehicle

        }));

    };

    const updateFleetTrends = (trends) => {

        const normalized = Array.isArray(trends[0])
            ? trends.flat()
            : trends;


        setFleetTrends(normalized);

    };



    const clearVehicles = () => {

        setVehicles({});

    };



    return (

        <DashboardContext.Provider

            value={{
                vehicles,
                recentEvents,
                fleetTrends,

                updateVehicle,
                updateRecentEvents,
                updateFleetTrends,

                clearVehicles,
            }}
        >

            {children}

        </DashboardContext.Provider>

    );

}



export function useDashboard() {


    const context = useContext(DashboardContext);


    if (!context) {

        throw new Error(
            "useDashboard must be used inside DashboardProvider"
        );

    }


    return context;

}