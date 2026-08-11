import { createContext, useContext, useEffect, useMemo, useRef, useCallback, useState } from "react";
import { subscribeToChannel, reconnectAll, getState } from "../websocket";
import { listVehicles, listVehicleHealth } from "../services/api/vehicleApi";
import { listDrivers, listDriverStatistics } from "../services/api/driverApi";
import { listMaintenance } from "../services/api/maintenanceApi";
import { listAlerts, acknowledgeAlert, resolveAlert } from "../services/api/alertApi";
import { listTelemetry } from "../services/api/telemetryApi";
import { listTrips } from "../services/api/tripApi";

const LiveDataContext = createContext(null);

function mergeTripsPayload(wsTrips, restTrips) {
  const rest = Array.isArray(restTrips) ? restTrips : [];
  const live = Array.isArray(wsTrips?.trips) ? wsTrips.trips : [];

  const byId = new Map();
  rest.forEach((t) => {
    if (t && t.trip_id) byId.set(t.trip_id, t);
  });
  live.forEach((t) => {
    if (t && t.trip_id) byId.set(t.trip_id, t);
  });

  const trips = Array.from(byId.values());

  if (wsTrips && live.length > 0 && rest.length === 0) {
    return wsTrips;
  }

  const totalDistance = trips.reduce((s, t) => s + (t.distance_km ?? 0), 0);
  const totalFuel = trips.reduce(
    (s, t) => s + (t.fuel_consumed_liters ?? 0),
    0
  );
  const scores = trips
    .map((t) => t.safety_score)
    .filter((v) => v != null);
  const avgScore =
    scores.length > 0
      ? scores.reduce((s, v) => s + v, 0) / scores.length
      : 0;

  return {
    timestamp: wsTrips?.timestamp ?? null,
    trips,
    total_trips: trips.length,
    total_distance_km: totalDistance,
    average_safety_score: avgScore,
    total_fuel_consumed_liters: totalFuel,
  };
}

function hasMaintenanceDue(maintenance, vehicleId, odometerKm) {
  const items = (maintenance || []).filter((m) => m.vehicle_id === vehicleId);
  if (items.length === 0) return false;
  return items.some((m) => {
    if (m.priority === "critical" || m.priority === "high") return true;
    if (m.due_odometer_km != null && odometerKm != null && m.due_odometer_km <= odometerKm) return true;
    return false;
  });
}

function buildFleetVehicles(vehicles, vehicleHealth, drivers, dashboardVehicles, maintenance) {
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
    const operationalStatus = live?.operational_status || "OFFLINE";
    const odometerKm = live?.odometer_km ?? null;

    const rawHealthScore = health?.overall_health_score ?? live?.overall_health_score ?? null;
    const overallHealthScore = rawHealthScore == null ? null : Math.round(rawHealthScore);

    return {
      vehicle_id: v.vehicle_id,
      registration_number: v.registration_number,
      vehicle_name: vehicleName,
      driver_id: v.driver_id ?? live?.driver_id ?? null,
      driver_name: driverName,
      operational_status: operationalStatus,
      trip_status: live?.trip_status ?? "active",
      maintenance_due: hasMaintenanceDue(maintenance, v.vehicle_id, odometerKm),
      odometer_km: odometerKm,
      overall_health_score: overallHealthScore,
      speed_kmh: live?.speed_kmh ?? 0,
      rpm: live?.rpm ?? 0,
      throttle_position_percent: live?.throttle_position_percent ?? null,
      brake_percent: live?.brake_percent ?? null,
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
  const [tripsSnapshot, setTripsSnapshot] = useState(null);
  const [restTrips, setRestTrips] = useState([]);
  const [dashboardConnectionState, setDashboardConnectionState] = useState("connecting");
  const [tripsConnectionState, setTripsConnectionState] = useState("connecting");

  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [driverStatistics, setDriverStatistics] = useState([]);
  const [vehicleHealth, setVehicleHealth] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [telemetry, setTelemetry] = useState([]);

  const [lastUpdate, setLastUpdate] = useState(null);
  const [syncing, setSyncing] = useState(false);

  const mountedRef = useRef(true);
  const lastUpdateRef = useRef(0);
  const syncingRef = useRef(false);
  const prevDashboardConnection = useRef("connecting");

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const updateLastUpdate = useCallback(() => {
    const now = Date.now();
    if (now - lastUpdateRef.current >= 1000) {
      lastUpdateRef.current = now;
      setLastUpdate(now);
    }
  }, []);

  useEffect(() => {
    const unsubscribeDashboard = subscribeToChannel(
      "dashboard",
      {
        onMessage: (message) => {
          if (message.type === "dashboard_snapshot" && message.data) {
            updateLastUpdate();
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
            setTripsSnapshot(message.data);
          }
        },
        onState: setTripsConnectionState,
      }
    );

    return () => {
      unsubscribeDashboard();
      unsubscribeTrips();
    };
  }, [updateLastUpdate]);

  const hydrate = useCallback(async () => {
    const results = await Promise.allSettled([
      listVehicles(),
      listDrivers(),
      listDriverStatistics(),
      listVehicleHealth(),
      listMaintenance(),
      listAlerts(),
      listTelemetry({ limit: 200 }),
      listTrips(),
    ]);
    if (!mountedRef.current) return;

    const [v, d, ds, vh, m, a, t, tr] = results;
    setVehicles(v.status === "fulfilled" ? v.value.data ?? [] : []);
    setDrivers(d.status === "fulfilled" ? d.value.data ?? [] : []);
    setDriverStatistics(ds.status === "fulfilled" ? ds.value.data ?? [] : []);
    setVehicleHealth(vh.status === "fulfilled" ? vh.value.data ?? [] : []);
    setMaintenance(m.status === "fulfilled" ? m.value.data ?? [] : []);
    setAlerts(a.status === "fulfilled" ? a.value.data ?? [] : []);
    setTelemetry(t.status === "fulfilled" ? t.value.data ?? [] : []);
    setRestTrips(tr.status === "fulfilled" ? tr.value.data ?? [] : []);
    if (results.some((r) => r.status === "fulfilled")) {
      updateLastUpdate();
    }
  }, [updateLastUpdate]);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    const prev = prevDashboardConnection.current;
    if (dashboardConnectionState === "live" && (prev === "connecting" || prev === "offline")) {
      hydrate();
    }
    prevDashboardConnection.current = dashboardConnectionState;
  }, [dashboardConnectionState, hydrate]);

  const waitForSettle = useCallback((timeoutMs = 5000) => {
    return new Promise((resolve) => {
      const started = Date.now();
      const tick = () => {
        const st = getState("dashboard");
        if (st === "live" || st === "offline" || Date.now() - started > timeoutMs) {
          resolve();
          return;
        }
        setTimeout(tick, 100);
      };
      tick();
    });
  }, []);

  const sync = useCallback(async () => {
    if (syncingRef.current) return;
    syncingRef.current = true;
    setSyncing(true);
    try {
      reconnectAll();
      await Promise.all([hydrate(), waitForSettle()]);
    } finally {
      syncingRef.current = false;
      setSyncing(false);
    }
  }, [hydrate, waitForSettle]);

  const connectionStatus = useMemo(() => {
    if (syncing) return "syncing";
    return dashboardConnectionState;
  }, [syncing, dashboardConnectionState]);

  const mergedFleet = useMemo(
    () => buildFleetVehicles(vehicles, vehicleHealth, drivers, dashboard?.vehicles, maintenance),
    [vehicles, vehicleHealth, drivers, dashboard, maintenance]
  );

  const fleetMeta = useMemo(() => buildFleetMeta(mergedFleet), [mergedFleet]);

  const trips = useMemo(
    () => mergeTripsPayload(tripsSnapshot, restTrips),
    [tripsSnapshot, restTrips]
  );

  const patchAlert = useCallback((alertId, patch) => {
    setAlerts((prev) =>
      (prev || []).map((a) =>
        a.alert_id === alertId ? { ...a, ...patch } : a
      )
    );
  }, []);

  const handleAcknowledgeAlert = useCallback(async (alertId) => {
    try {
      const result = await acknowledgeAlert(alertId);
      if (result?.data) patchAlert(alertId, result.data);
      else patchAlert(alertId, { acknowledged: true });
    } catch (error) {
      console.error("[alerts] acknowledge failed", alertId, error);
    }
  }, [patchAlert]);

  const handleResolveAlert = useCallback(async (alertId) => {
    try {
      const result = await resolveAlert(alertId);
      if (result?.data) patchAlert(alertId, result.data);
      else patchAlert(alertId, { status: "resolved", acknowledged: true, resolved_at: new Date().toISOString() });
    } catch (error) {
      console.error("[alerts] resolve failed", alertId, error);
    }
  }, [patchAlert]);

  const removeTrip = useCallback((tripId) => {
    setRestTrips((prev) =>
      (prev || []).filter((t) => t?.trip_id !== tripId)
    );
  }, []);

  const value = {
    dashboard,
    trips,
    removeTrip,
    vehicles,
    drivers,
    driverStatistics,
    vehicleHealth,
    maintenance,
    alerts,
    telemetry,
    connectionStatus,
    tripsConnectionState,
    lastUpdate,
    syncing,
    sync,
    mergedFleet,
    fleetMeta,
    acknowledgeAlert: handleAcknowledgeAlert,
    resolveAlert: handleResolveAlert,
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
