import useDashboardSocket from "../hooks/useDashboardSocket";

export default function Dashboard() {
  const { fleet, connected } = useDashboardSocket(
    "ws://localhost:8000/ws/dashboard"
  );


  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1>DriveVitals Fleet Control</h1>

        <div style={{
          padding: "6px 12px",
          borderRadius: "20px",
          background: connected ? "#00c853" : "#d50000",
          color: "white",
          fontSize: "12px"
        }}>
          {connected ? "LIVE" : "OFFLINE"}
        </div>
      </header>

      <div style={styles.grid}>
        {Object.values(fleet).map((v) => (
          <div key={v.vehicle_id} style={styles.card}>
            <h3>{v.vehicle_id}</h3>

            <p>🚗 Speed: {v?.telemetry?.speed_kmh?.toFixed?.(1) ?? 0} km/h</p>
            <p>⚙️ RPM: {v?.telemetry?.rpm ?? 0}</p>
            <p>🧠 Mode: {v?.telemetry?.phase ?? "N/A"}</p>
            <p>⛽ Fuel Rate: {v?.telemetry?.fuel_rate_lph ?? 0}</p>
            <p
              style={{
                color:
                   v?.vehicle_health?.health === "healthy"
                     ? "#00c853"
                     : "#ff5252",
                }}
            >
                {v?.vehicle_health?.health ?? "unknown"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  container: {
    background: "#0b0f14",
    minHeight: "100vh",
    color: "white",
    padding: "20px",
    fontFamily: "Arial"
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center"
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
    gap: "16px",
    marginTop: "20px"
  },
  card: {
    background: "#121821",
    padding: "16px",
    borderRadius: "12px",
    border: "1px solid #1f2a36"
  }
};