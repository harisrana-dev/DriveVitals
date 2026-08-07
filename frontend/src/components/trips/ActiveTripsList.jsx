import { memo } from 'react';
import { ChevronRight, MapPin, Clock, Gauge, Activity } from 'lucide-react';

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '—';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  if (mins > 0) return `${mins}m`;
  return `${seconds}s`;
}

function formatDistance(km) {
  if (km == null || km <= 0) return '—';
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

const EVENT_CHIPS = [
  { key: 'speeding', label: 'Speeding' },
  { key: 'harshBraking', label: 'Harsh Brake' },
  { key: 'aggressiveThrottle', label: 'Aggr. Throttle' },
  { key: 'highRpm', label: 'High RPM' },
];

export const ActiveTripsList = memo(function ActiveTripsList({ trips, onTripClick, selectedTripId }) {
  if (!trips || trips.length === 0) return null;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}
    >
      {trips.map((trip, i) => {
        const activeEvents = EVENT_CHIPS.filter((chip) => trip[chip.key] > 0);
        return (
          <div
            key={trip.id}
            className={`fade-in stagger-${Math.min(i + 1, 6)}`}
            onClick={() => onTripClick(trip)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: '12px 16px',
              borderRadius: 10,
              background: selectedTripId === trip.id
                ? 'var(--color-accent-subtle)'
                : 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              if (selectedTripId !== trip.id) e.currentTarget.style.background = 'var(--color-surface-hover)';
            }}
            onMouseLeave={(e) => {
              if (selectedTripId !== trip.id) e.currentTarget.style.background = 'var(--color-surface)';
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: 'var(--color-green)',
                boxShadow: '0 0 0 0 rgba(52,211,153,0.5)',
                animation: 'pulse-dot 2s infinite',
                flexShrink: 0,
              }}
            />
            <div style={{ minWidth: 0, flex: '0 1 220px' }}>
              <div style={{ fontWeight: 500, color: 'var(--color-text-primary)', fontFamily: 'monospace', fontSize: 12 }}>
                {trip.id}
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {trip.driverName}
              </div>
            </div>
            <div style={{ minWidth: 0, flex: '1 1 180px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--color-text-primary)', fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                <MapPin size={12} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {trip.routeName || trip.routeType}
                </span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 1 }}>
                {trip.vehicleName}
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
              <Clock size={12} style={{ color: 'var(--color-text-muted)' }} />
              <span>{formatDuration(trip.duration)}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
              <Gauge size={12} style={{ color: 'var(--color-text-muted)' }} />
              <span>{trip.averageSpeed > 0 ? `${trip.averageSpeed.toFixed(0)} km/h` : '—'}</span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
              {formatDistance(trip.distance)}
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', flex: '1 1 140px' }}>
              {activeEvents.length === 0 ? (
                <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                  <Activity size={11} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                  No events
                </span>
              ) : (
                activeEvents.map((chip) => (
                  <span
                    key={chip.key}
                    style={{
                      fontSize: 10,
                      fontWeight: 600,
                      padding: '2px 7px',
                      borderRadius: 20,
                      background: 'var(--color-red-bg)',
                      color: 'var(--color-red)',
                    }}
                  >
                    {chip.label}
                  </span>
                ))
              )}
            </div>
            <div style={{ color: 'var(--color-text-muted)', flexShrink: 0 }}>
              <ChevronRight size={14} />
            </div>
          </div>
        );
      })}
    </div>
  );
});
