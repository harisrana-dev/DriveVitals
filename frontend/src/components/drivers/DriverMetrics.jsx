import { memo } from 'react';
import { Route, Map, Gauge, Fuel, Clock, ShieldCheck } from 'lucide-react';
import { formatFuelEfficiency, formatDuration, formatSpeed } from '../../utils/formatters';

export const DriverMetrics = memo(function DriverMetrics({ driver }) {
  const h = driver.historical || {};
  const metrics = [
    { icon: <Route size={14} />, label: 'Total Distance', value: formatKm(h.totalDistanceKm) },
    { icon: <Map size={14} />, label: 'Trips Completed', value: formatTrips(h.tripsCompleted) },
    { icon: <Gauge size={14} />, label: 'Average Speed', value: formatSpeedRaw(h.averageSpeedKmh) },
    { icon: <Fuel size={14} />, label: 'Fuel Efficiency', value: formatFuelEfficiency(h.fuelEfficiency) },
    { icon: <ShieldCheck size={14} />, label: 'Average Trip Score', value: formatScore(h.averageTripScore) },
    { icon: <Clock size={14} />, label: 'Driving Hours', value: formatHours(h.drivingHours) },
  ];

  return (
    <>
      {metrics.map((m) => (
        <div
          key={m.label}
          style={{
            padding: '8px 10px',
            borderRadius: 8,
            background: 'var(--color-bg)',
            border: '1px solid var(--color-border-light)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              color: 'var(--color-text-muted)',
              marginBottom: 3,
            }}
          >
            {m.icon}
            <span style={{ fontSize: 10 }}>{m.label}</span>
          </div>
          <div
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {m.value}
          </div>
        </div>
      ))}
    </>
  );
});

function formatKm(km) {
  if (km == null) return '—';
  if (km >= 1000) return `${(km / 1000).toFixed(1)}k km`;
  return `${Math.round(km)} km`;
}

function formatTrips(trips) {
  if (trips == null) return '—';
  return trips.toString();
}

function formatSpeedRaw(speed) {
  if (speed == null) return '—';
  return `${speed} km/h`;
}

function formatScore(score) {
  if (score == null) return '—';
  return `${Math.round(score)}/100`;
}

function formatHours(h) {
  if (h == null) return '—';
  const hours = Math.floor(h);
  const mins = Math.round((h - hours) * 60);
  if (hours === 0) return `${mins}m`;
  return `${hours}h ${mins}m`;
}
