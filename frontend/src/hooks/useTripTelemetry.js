import { useEffect, useMemo, useState, useRef } from 'react';
import { listTelemetry } from '../services/api/telemetryApi';

function toChartRows(samples) {
  const chronological = [...(samples || [])].sort(
    (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
  );

  const maxPoints = 360;
  const rows = chronological.map((s) => ({
    t: new Date(s.timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
    speed: s.speed_kmh ?? 0,
    rpm: s.rpm ?? 0,
    throttle: s.throttle_percent ?? 0,
    brake: s.brake_percent ?? 0,
    load: s.engine_load_percent ?? 0,
    fuelRate: s.fuel_rate_lph ?? 0,
    coolant: s.coolant_temperature_c ?? 0,
    fuelLevel: s.fuel_level_percent ?? 0,
  }));

  if (rows.length <= maxPoints) return rows;
  const step = rows.length / maxPoints;
  const downsampled = [];
  for (let i = 0; i < maxPoints; i += 1) {
    downsampled.push(rows[Math.floor(i * step)]);
  }
  return downsampled;
}

export function useTripTelemetry(tripId, { active = false } = {}) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(() => tripId != null);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  useEffect(() => {
    if (!tripId) {
      return undefined;
    }

    let disposed = false;
    const controller = new AbortController();
    abortRef.current = controller;

    const load = async () => {
      try {
        const result = await listTelemetry(
          { trip_id: tripId, limit: 1500 },
          { signal: controller.signal }
        );
        if (!disposed && !controller.signal.aborted) {
          setRows(toChartRows(result?.data ?? []));
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (!disposed && !controller.signal.aborted && err?.name !== 'AbortError') {
          setError(err);
          setLoading(false);
        }
      }
    };

    load();

    let timer = null;
    if (active) {
      timer = setInterval(load, 5000);
    }

    return () => {
      disposed = true;
      if (timer) clearInterval(timer);
      controller.abort();
    };
  }, [tripId, active]);

  const summary = useMemo(() => {
    if (!rows || rows.length === 0) {
      return {
        maxSpeed: 0,
        maxRpm: 0,
        avgLoad: 0,
        maxCoolant: 0,
      };
    }
    let maxSpeed = 0;
    let maxRpm = 0;
    let loadSum = 0;
    let maxCoolant = 0;
    for (const r of rows) {
      if (r.speed > maxSpeed) maxSpeed = r.speed;
      if (r.rpm > maxRpm) maxRpm = r.rpm;
      loadSum += r.load;
      if (r.coolant > maxCoolant) maxCoolant = r.coolant;
    }
    return {
      maxSpeed,
      maxRpm,
      avgLoad: loadSum / rows.length,
      maxCoolant,
    };
  }, [rows]);

  return { rows, summary, loading, error };
}
