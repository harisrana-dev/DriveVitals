import { createContext, useContext, useState } from "react";

const TripsContext = createContext(null);

export function TripsProvider({ children }) {
    const [tripsData, setTripsData] = useState(null);
    return (
        <TripsContext.Provider
            value={{
                tripsData,
                setTripsData
            }}
        >
            {children}
        </TripsContext.Provider>
    );
}

export function useTripsContext() {
    return useContext(TripsContext);
}
