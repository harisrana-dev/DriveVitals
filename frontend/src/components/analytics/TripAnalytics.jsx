import { memo } from 'react';
import { MapPin, Clock, Fuel, AlertTriangle } from 'lucide-react';
import { formatDuration } from '../../utils/formatters';

export const TripAnalytics = memo(function TripAnalytics({ tripSummary }) {
  if (!tripSummary) {
    return (
      <div style={{
        padding: '16px 20px',
        borderRadius: 14,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
      }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 8 }}>
          Trip Analytics
        </h2>
        <div style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>Loading trip data...</div>
      </div>
    );
  }

  if (tripSummary.data_quality === 'no_data') {
    return (
      <div style={{
        padding: '16px 20px',
        borderRadius: 14,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
      }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 8 }}>
          Trip Analytics
        </h2>
        <div style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>No completed trips in this period</div>
      </div>
    );
  }

  const metrics = [
    {
      icon: <MapPin size={14} />,
      label: 'Completed Trips',
      value: tripSummary.completed_trips,
      color: 'var(--color-blue)',
    },
    {
      icon: <AlertTriangle size={14} />,
      label: 'Aborted Trips',
      value: tripSummary.aborted_trips,
      color: 'var(--color-amber)',
    },
    {
      icon: null,
      label: 'Total Distance',
      value: tripSummary.total_distance_km != null ? `${tripSummary.total_distance_km} km` : '—',
      color: 'var(--color-text-primary)',
    },
    {
      icon: null,
      label: 'Avg Trip Distance',
      value: tripSummary.avg_distance_km != null ? `${tripSummary.avg_distance_km} km` : '—',
      color: 'var(--color-text-primary)',
    },
    {
      icon: <Clock size={14} />,
      label: 'Avg Duration',
      value: tripSummary.avg_duration_seconds != null ? formatDuration(tripSummary.avg_duration_seconds) : '—',
      color: 'var(--color-text-primary)',
    },
    {
      icon: <Clock size={14} />,
      label: 'Total Driving Time',
      value: tripSummary.total_driving_time_seconds != null ? formatDuration(tripSummary.total_driving_time_seconds) : '—',
      color: 'var(--color-text-primary)',
    },
    {
      icon: <Fuel size={14} />,
      label: 'Avg Fuel Efficiency',
      value: tripSummary.avg_fuel_efficiency != null ? `${tripSummary.avg_fuel_efficiency} km/L` : '—',
      color: 'var(--color-green)',
    },
    {
      icon: null,
      label: 'Events per Trip',
      value: tripSummary.events_per_trip != null ? tripSummary.events_per_trip.toFixed(1) : '—',
      color: 'var(--color-amber)',
    },
    {
      icon: null,
      label: 'Events / 100 km',
      value: tripSummary.events_per_100km != null ? tripSummary.events_per_100km.toFixed(1) : '—',
      color: 'var(--color-red)',
    },
  ];

  return (
    <div>
      <h2 style={{
        fontSize: 14,
        fontWeight: 700,
        color: 'var(--color-text-primary)',
        marginBottom: 12,
        letterSpacing: '-0.01em',
      }}>
        Trip Analytics
      </h2>
      <div style={{
        padding: '16px 20px',
        borderRadius: 14,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: 12,
        }}>
          {metrics.map((m) => (
            <div key={m.label} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                fontSize: 11,
                fontWeight: 600,
                color: 'var(--color-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.03em',
              }}>
                {m.icon && <span style={{ color: m.color }}>{m.icon}</span>}
                {m.label}
              </div>
              <div style={{
                fontSize: 18,
                fontWeight: 700,
                color: 'var(--color-text-primary)',
                lineHeight: 1.2,
              }}>
                {m.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});
