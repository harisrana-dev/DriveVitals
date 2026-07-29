import { memo } from 'react';
import { Route, Map, Gauge, Fuel, Clock } from 'lucide-react';

export const DriverMetrics = memo(function DriverMetrics({ driver }) {
  const metrics = [
    { icon: <Route size={14} />, label: 'Total Distance', value: formatKm(driver.totalDistanceKm) },
    { icon: <Map size={14} />, label: 'Trips Completed', value: driver.tripsCompleted.toString() },
    { icon: <Gauge size={14} />, label: 'Average Speed', value: `${driver.averageSpeedKmh} km/h` },
    { icon: <Fuel size={14} />, label: 'Fuel Efficiency', value: `${driver.fuelEfficiencyKmPerL} km/L` },
    { icon: <Clock size={14} />, label: 'Driving Hours', value: formatHours(driver.drivingHours) },
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
  if (km >= 1000) return `${(km / 1000).toFixed(1)}k km`;
  return `${km.toFixed(0)} km`;
}

function formatHours(h) {
  const hours = Math.floor(h);
  const mins = Math.round((h - hours) * 60);
  if (hours === 0) return `${mins}m`;
  return `${hours}h ${mins}m`;
}
