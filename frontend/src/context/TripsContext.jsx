import { useLiveData } from "./useLiveData";
import { TripsContext } from "./tripsCtx";

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
