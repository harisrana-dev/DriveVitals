import { createContext, useContext, useState } from "react";


const DashboardContext = createContext(null);



export function DashboardProvider({ children }) {


    const [vehicles, setVehicles] = useState({});
    const [recentEvents, setRecentEvents] = useState([]);

    const updateRecentEvents = (events) => {
        setRecentEvents(events);
    };

    const updateVehicle = (vehicle) => {

        setVehicles((previous) => ({

            ...previous,

            [vehicle.vehicle_id]: vehicle

        }));

    };



    const clearVehicles = () => {

        setVehicles({});

    };



    return (

        <DashboardContext.Provider

            value={{
                vehicles,
                recentEvents,
                updateVehicle,
                updateRecentEvents,
                clearVehicles
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