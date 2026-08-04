import { createContext, useContext } from "react";
import { useLiveData } from "./LiveDataContext";

const FleetContext = createContext(null);

export function FleetProvider({ children }) {

    const {
        dashboard
    } = useLiveData();

    return (
        <FleetContext.Provider
            value={{
                dashboard
            }}
        >
            {children}
        </FleetContext.Provider>
    );
}


export function useFleetContext(){

    return useContext(FleetContext);

}
