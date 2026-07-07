import { useEffect, useRef, useState } from "react";

console.log("📦 useDashboardSocket module loaded");

export default function useDashboardSocket(url) {
    const socketRef = useRef(null);

    const [fleet, setFleet] = useState({});
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        console.log("🚀 useDashboardSocket started");
        console.log("Connecting to:", url);

        const ws = new WebSocket(url);
        socketRef.current = ws;

        ws.onopen = () => {
            console.log("🟢 WebSocket OPEN");
            setConnected(true);
        };

        ws.onmessage = (event) => {
            console.log("📨 Raw message:", event.data);

            try {
                const data = JSON.parse(event.data);

                console.log("✅ Parsed message:", data);

                if (
                    data.type === "vehicle_update" &&
                    data.vehicle &&
                    data.vehicle.vehicle_id
                ) {
                    setFleet((prev) => ({
                        ...prev,
                        [data.vehicle.vehicle_id]: data.vehicle,
                    }));

                    console.log(
                        "🚗 Updated vehicle:",
                        data.vehicle.vehicle_id
                    );
                } else {
                    console.log("⚠️ Unknown message:", data);
                }
            } catch (err) {
                console.error("❌ JSON parse error:", err);
            }
        };

        ws.onerror = (event) => {
            console.error("❌ WebSocket Error:", event);
        };

        ws.onclose = (event) => {
            console.log(
                "🔴 WebSocket Closed",
                "Code:",
                event.code,
                "Reason:",
                event.reason
            );

            setConnected(false);
        };

        return () => {
            console.log("Closing WebSocket...");
            ws.close();
        };
    }, [url]);

    return {
        fleet,
        connected,
    };
}