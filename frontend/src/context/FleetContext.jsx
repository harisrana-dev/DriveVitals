import { useLiveData } from "./useLiveData";
import { FleetContext } from "./fleetCtx";

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
