import { useEffect } from "react";

import { dashboardSocket } 
from "../services/websocket";

import { useDashboard }
from "../context/DashboardContext";



export default function useDashboardSocket(){


    const {
        updateVehicle
    } = useDashboard();



    useEffect(()=>{


        dashboardSocket.connect();



        const unsubscribe =
        dashboardSocket.subscribe(
            (message)=>{


                if(
                    message.type === "vehicle_update"
                ){
                    console.log("🚗 Updating vehicle:", message.vehicle);
                    
                    updateVehicle(
                        message.vehicle
                    );

                } 


            }
        );



        return ()=>{

            unsubscribe();

            dashboardSocket.disconnect();

        };


    },[]);


}