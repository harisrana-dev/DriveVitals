import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { subscribeToChannel } from "../websocket";
import { listVehicles, listVehicleHealth } from "../services/api/vehicleApi";
import { listDrivers, listDriverStatistics } from "../services/api/driverApi";
import { listMaintenance } from "../services/api/maintenanceApi";
import { listAlerts } from "../services/api/alertApi";
import { listTelemetry } from "../services/api/telemetryApi";

const LiveDataContext = createContext(null);

function buildFleetVehicles(vehicles, vehicleHealth, drivers, dashboardVehicles) {
  if (!Array.isArray(vehicles)) return [];

  const healthById = new Map((vehicleHealth || []).map((h) => [h.vehicle_id, h]));
  const liveById = new Map((dashboardVehicles || []).map((v) => [v.vehicle_id, v]));
  const driverById = new Map((drivers || []).map((d) => [d.driver_id, d]));

  return vehicles.map((v) => {
    const health = healthById.get(v.vehicle_id);
    const live = liveById.get(v.vehicle_id);
    const driver = v.driver_id ? driverById.get(v.driver_id) : null;

    const vehicleName =
      live?.vehicle_name ||
      (v.manufacturer && v.model ? `${v.manufacturer} ${v.model}`.trim() : v.registration_number || v.vehicle_id);
    const driverName =
      live?.driver_name || (driver ? `${driver.first_name} ${driver.last_name}`.trim() : null);
    const operationalStatus = live?.operational_status || (v.status === "active" ? "ACTIVE" : "INACTIVE");

    const rawHealthScore = health?.overall_health_score ?? live?.overall_health_score ?? null;
    const overallHealthScore = rawHealthScore == null ? null : Math.round(rawHealthScore);

    return {
      vehicle_id: v.vehicle_id,
      registration_number: v.registration_number,
      vehicle_name: vehicleName,
      driver_id: v.driver_id ?? live?.driver_id ?? null,
      driver_name: driverName,
      operational_status: operationalStatus,
      odometer_km: live?.odometer_km ?? null,
      overall_health_score: overallHealthScore,
      speed_kmh: live?.speed_kmh ?? 0,
      rpm: live?.rpm ?? 0,
      throttle_position_percent: live?.throttle_position_percent ?? null,
      brake_pressure: live?.brake_pressure ?? null,
      fuel_level_percent: live?.fuel_level_percent ?? null,
      coolant_temperature_c: live?.coolant_temperature_c ?? null,
      engine_load_percent: live?.engine_load_percent ?? null,
      active_alert_count: live?.active_alert_count ?? 0,
      active_alert_text: live?.active_alert_text ?? null,
      active_event_types: live?.active_event_types || [],
      speeding: live?.speeding ?? false,
      aggressive_throttle: live?.aggressive_throttle ?? false,
      harsh_braking: live?.harsh_braking ?? false,
      high_rpm: live?.high_rpm ?? false,
      last_updated_at: live?.last_updated_at ?? null,
    };
  });
}

function buildFleetMeta(mergedFleet) {
  const meta = {};
  for (const v of mergedFleet) {
    meta[v.vehicle_id] = {
      vehicle_name: v.vehicle_name,
      driver_id: v.driver_id,
      driver_name: v.driver_name,
      odometer_km: v.odometer_km,
      overall_health_score: v.overall_health_score,
    };
  }
  return meta;
}

export function LiveDataProvider({ children }) {
  const [dashboard, setDashboard] = useState(null);
  const [trips, setTrips] = useState(null);
  const [dashboardConnectionState, setDashboardConnectionState] = useState("connecting");
  const [tripsConnectionState, setTripsConnectionState] = useState("connecting");

  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [driverStatistics, setDriverStatistics] = useState([]);
  const [vehicleHealth, setVehicleHealth] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [telemetry, setTelemetry] = useState([]);
  const [restState, setRestState] = useState("loading");

  useEffect(() => {
    const unsubscribeDashboard = subscribeToChannel(
      "dashboard",
      {
        onMessage: (message) => {
          if (message.type === "dashboard_snapshot" && message.data) {
            setDashboard(message.data);
          }
        },
        onState: setDashboardConnectionState,
      }
    );

    const unsubscribeTrips = subscribeToChannel(
      "trips",
      {
        onMessage: (message) => {
          if (message.type === "trips_snapshot" && message.data) {
            setTrips(message.data);
          }
        },
        onState: setTripsConnectionState,
      }
    );

    return () => {
      unsubscribeDashboard();
      unsubscribeTrips();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function hydrate() {
      const results = await Promise.allSettled([
        listVehicles(),
        listDrivers(),
        listDriverStatistics(),
        listVehicleHealth(),
        listMaintenance(),
        listAlerts(),
        listTelemetry({ limit: 200 }),
      ]);
      if (cancelled) return;

      const [v, d, ds, vh, m, a, t] = results;
      setVehicles(v.status === "fulfilled" ? v.value.data ?? [] : []);
      setDrivers(d.status === "fulfilled" ? d.value.data ?? [] : []);
      setDriverStatistics(ds.status === "fulfilled" ? ds.value.data ?? [] : []);
      setVehicleHealth(vh.status === "fulfilled" ? vh.value.data ?? [] : []);
      setMaintenance(m.status === "fulfilled" ? m.value.data ?? [] : []);
      setAlerts(a.status === "fulfilled" ? a.value.data ?? [] : []);
      setTelemetry(t.status === "fulfilled" ? t.value.data ?? [] : []);
      setRestState(results.some((r) => r.status === "fulfilled") ? "loaded" : "failed");
    }

    hydrate();
    return () => {
      cancelled = true;
    };
  }, []);

  const mergedFleet = useMemo(
    () => buildFleetVehicles(vehicles, vehicleHealth, drivers, dashboard?.vehicles),
    [vehicles, vehicleHealth, drivers, dashboard]
  );

  const fleetMeta = useMemo(() => buildFleetMeta(mergedFleet), [mergedFleet]);

  const dataSource = useMemo(() => {
    const hasLiveVehicles = Array.isArray(dashboard?.vehicles) && dashboard.vehicles.length > 0;
    const source = (live, count) => (live ? "live" : count > 0 ? "rest" : "empty");
    return {
      dashboard: source(hasLiveVehicles, mergedFleet.length),
      trips: source(tripsConnectionState === "connected" && !!trips, trips ? 1 : 0),
      fleet: source(hasLiveVehicles, mergedFleet.length),
      vehicleHealth: source(false, vehicleHealth.length),
      maintenance: source(false, maintenance.length),
      alerts: source(false, alerts.length),
      drivers: source(false, drivers.length),
      telemetry: source(false, telemetry.length),
    };
  }, [dashboard, trips, tripsConnectionState, mergedFleet, vehicleHealth, maintenance, alerts, drivers, telemetry]);

  const overallStatus = useMemo(() => {
    const values = Object.values(dataSource);
    if (values.includes("live")) return "live";
    if (values.includes("rest")) return "rest";
    return "offline";
  }, [dataSource]);

  const value = {
    dashboard,
    trips,
    vehicles,
    drivers,
    driverStatistics,
    vehicleHealth,
    maintenance,
    alerts,
    telemetry,
    connectionState: { dashboard: dashboardConnectionState, trips: tripsConnectionState },
    dataSource,
    overallStatus,
    restState,
    mergedFleet,
    fleetMeta,
  };

  return (
    <LiveDataContext.Provider value={value}>
      {children}
    </LiveDataContext.Provider>
  );
}

export function useLiveData() {
  return useContext(LiveDataContext);
}
