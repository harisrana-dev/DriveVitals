export default function FleetOverview({ fleet }) {

  const vehicles = Object.values(fleet);


  const totalVehicles = vehicles.length;


  const healthyVehicles = vehicles.filter(
    (v) =>
      v?.vehicle_health?.health === "healthy"
  ).length;


  const avgSpeed =
    vehicles.length > 0
      ?
      (
        vehicles.reduce(
          (sum, v) =>
            sum + (v?.telemetry?.speed_kmh || 0),
          0
        ) / vehicles.length
      ).toFixed(1)
      :
      0;



  return (
    <div style={styles.container}>

      <StatCard
        title="ACTIVE VEHICLES"
        value={totalVehicles}
      />

      <StatCard
        title="HEALTHY VEHICLES"
        value={`${healthyVehicles}/${totalVehicles}`}
      />

      <StatCard
        title="AVERAGE SPEED"
        value={`${avgSpeed} km/h`}
      />

      <StatCard
        title="SYSTEM STATUS"
        value="LIVE"
      />


    </div>
  );
}



function StatCard({title,value}){

  return (
    <div style={styles.card}>
      <p style={styles.title}>
        {title}
      </p>

      <h2>
        {value}
      </h2>
    </div>
  );
}



const styles = {

  container:{
    display:"grid",
    gridTemplateColumns:
      "repeat(auto-fit,minmax(200px,1fr))",
    gap:"20px",
    marginTop:"25px",
    marginBottom:"25px"
  },


  card:{
    background:"#121821",
    padding:"20px",
    borderRadius:"16px",
    border:"1px solid #1f2a36"
  },


  title:{
    fontSize:"12px",
    color:"#9ca3af",
    letterSpacing:"1px"
  }

};