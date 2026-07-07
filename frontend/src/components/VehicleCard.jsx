export default function VehicleCard({ vehicle }) {

  const telemetry = vehicle?.telemetry || {};
  const health = vehicle?.vehicle_health || {};
  const fuel = vehicle?.fuel_efficiency || {};
  const driver = vehicle?.driver_behaviour || {};


  return (
    <div style={styles.card}>

      {/* Header */}
      <div style={styles.header}>

        <h3>
          🚗 {vehicle.vehicle_id}
        </h3>

        <span
          style={{
            ...styles.status,
            background:
              health.health === "healthy"
              ? "#00c853"
              : "#ff5252"
          }}
        >
          {health.health || "unknown"}
        </span>

      </div>


      {/* Speed */}
      <div style={styles.speedBox}>

        <h1>
          {telemetry.speed_kmh?.toFixed(0) || 0}
        </h1>

        <p>
          km/h
        </p>

      </div>



      {/* Metrics */}
      <div style={styles.metrics}>

        <Metric
          label="RPM"
          value={telemetry.rpm}
        />

        <Metric
          label="GEAR"
          value={telemetry.gear}
        />

        <Metric
          label="LOAD"
          value={`${telemetry.engine_load || 0}%`}
        />

        <Metric
          label="EFFICIENCY"
          value={`${fuel.km_per_liter || 0} km/L`}
        />

      </div>



      {/* Driving Mode */}
      <div style={styles.footer}>

        🧠 {telemetry.phase || "unknown"}

      </div>


    </div>
  );
}



function Metric({label,value}){

  return (

    <div>

      <p style={styles.label}>
        {label}
      </p>

      <strong>
        {value ?? 0}
      </strong>

    </div>

  );

}



const styles = {


card:{
  background:"#121821",
  borderRadius:"20px",
  padding:"20px",
  border:"1px solid #1f2a36",
},


header:{
  display:"flex",
  justifyContent:"space-between",
  alignItems:"center"
},


status:{
  padding:"5px 12px",
  borderRadius:"20px",
  fontSize:"12px",
  color:"white"
},


speedBox:{
  textAlign:"center",
  margin:"25px 0"
},


metrics:{
  display:"grid",
  gridTemplateColumns:"1fr 1fr",
  gap:"15px"
},


label:{
  color:"#9ca3af",
  fontSize:"12px"
},


footer:{
  marginTop:"20px",
  color:"#d1d5db"
}


};