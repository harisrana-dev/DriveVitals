import { useEffect } from "react";

import { dashboardSocket } 
from "../services/websocket";

import { useDashboard }
from "../context/DashboardContext";



export default function useDashboardSocket(){


    const {
        updateVehicle,
        updateRecentEvents
    } = useDashboard();



    useEffect(()=>{


        dashboardSocket.connect();



        const unsubscribe =
        dashboardSocket.subscribe((message) => {

            console.log("📩 Received WebSocket message:", message);

            if (message.type === "dashboard_update") {

                 console.log("🚗 Vehicle:", message.vehicle);
                 console.log("📋 Recent Events:", message.recent_events);

                 updateVehicle(message.vehicle);
                 updateRecentEvents(message.recent_events);

            } else {

                console.log("⚠️ Unknown message type:", message.type);

            }

        });



        return ()=>{

            unsubscribe();

            dashboardSocket.disconnect();

        };


    },[]);


}