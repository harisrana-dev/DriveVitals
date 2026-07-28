import {
    createContext,
    useContext,
} from "react";

import {
    useDashboardSocket
} from "../hooks/useDashboardSocket";


const DashboardContext =
createContext(null);



export function DashboardProvider({
    children
}){


    const dashboardData =
        useDashboardSocket();



    return (

        <DashboardContext.Provider
            value={dashboardData}
        >

            {children}

        </DashboardContext.Provider>

    );

}



export function useDashboard(){

    return useContext(
        DashboardContext
    );

}