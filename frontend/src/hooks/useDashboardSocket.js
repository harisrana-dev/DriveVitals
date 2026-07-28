import { useEffect } from "react";
import { useFleetContext } from "../context/FleetContext";


export function useDashboardSocket(){

    const {
        setDashboard
    } = useFleetContext();


    useEffect(()=>{

        const socket = new WebSocket(
            "ws://localhost:8000/ws/dashboard"
        );


        socket.onmessage = (event)=>{

            const message = JSON.parse(
                event.data
            );


            if(
                message.type === "dashboard_snapshot"
                && message.data
            ){
                setDashboard(message.data);
            }

        };


        return ()=>socket.close();


    },[setDashboard]);

}