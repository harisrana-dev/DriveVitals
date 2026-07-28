import { createContext, useContext, useState } from "react";

const FleetContext = createContext(null);

export function FleetProvider({ children }) {

    const [dashboard, setDashboard] = useState(null);

    return (
        <FleetContext.Provider
            value={{
                dashboard,
                setDashboard
            }}
        >
            {children}
        </FleetContext.Provider>
    );
}


export function useFleetContext(){

    return useContext(FleetContext);

}