import { memo } from 'react';
import { useAlerts } from '../../hooks/useAlerts';

export const DrivingEventsFeed = memo(function DrivingEventsFeed() {
  const { drivingEvents } = useAlerts();

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 14 }}>
        Live Driving Events
        <span style={{ fontSize: 11, fontWeight: 400, color: 'var(--color-text-muted)', marginLeft: 8 }}>
          Latest 10
        </span>
      </div>
      <div
        style={{
          maxHeight: 260,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 4,
        }}
      >
        {drivingEvents.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 0' }}>
            No recent driving events.
          </div>
        ) : (
          drivingEvents.map((evt) => (
            <div
              key={evt.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '6px 8px',
                borderRadius: 6,
                fontSize: 12,
              }}
            >
              <span
                style={{
                  fontSize: 11,
                  color: 'var(--color-text-muted)',
                  fontVariantNumeric: 'tabular-nums',
                  fontFamily: 'monospace',
                  minWidth: 45,
                  flexShrink: 0,
                }}
              >
                {new Date(evt.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              <span style={{ color: 'var(--color-text-secondary)', fontWeight: 500, minWidth: 50, flexShrink: 0 }}>
                {evt.vehicle_id}
              </span>
              <span style={{ color: 'var(--color-text-primary)' }}>{evt.eventType}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
});
