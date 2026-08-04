import { createContext, useContext } from "react";
import { useLiveData } from "./LiveDataContext";

const TripsContext = createContext(null);

export function TripsProvider({ children }) {
    const {
        trips
    } = useLiveData();

    return (
        <TripsContext.Provider
            value={{
                tripsData: trips
            }}
        >
            {children}
        </TripsContext.Provider>
    );
}

export function useTripsContext() {
    return useContext(TripsContext);
}
