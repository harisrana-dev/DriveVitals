import useDashboardSocket from "../hooks/useDashboardSocket";
import FleetOverview from "../components/FleetOverview";
import VehicleCard from "../components/VehicleCard";

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
      <FleetOverview fleet={fleet}/>

      <div style={styles.grid}>
          {Object.values(fleet).map((v) => (
             <VehicleCard
                key={v.vehicle_id}
                vehicle={v}
             />
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

};