import { useEffect } from "react";
import { useTripsContext } from "../context/TripsContext";

export function useTripsSocket() {
    const {
        setTripsData
    } = useTripsContext();

    useEffect(() => {
        const socket = new WebSocket(
            "ws://localhost:8000/ws/trips"
        );

        socket.onmessage = (event) => {
            const message = JSON.parse(
                event.data
            );

            if (
                message.type === "trips_snapshot"
                && message.data
            ) {
                setTripsData(message.data);
            }
        };

        return () => socket.close();
    }, [setTripsData]);
}
