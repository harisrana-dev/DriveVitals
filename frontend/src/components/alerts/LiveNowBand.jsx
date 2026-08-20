import { memo } from 'react';
import { Radio } from 'lucide-react';
import { useLiveEvents } from '../../hooks/useAlerts';
import { useLiveData } from '../../context/useLiveData';

/**
 * LIVE NOW band. The single place on the page allowed a pulse. It renders
 * live driving events taken verbatim from the backend fleet snapshot's
 * `active_event_types`; there are no timestamps for these events, so they
 * are shown as presence, never as "3 min ago". When the socket is not
 * connected the pulse is removed and the state is labelled Disconnected.
 *
 * Live presence is subscribed here in isolation (via `useLiveEvents`), so
 * a new dashboard snapshot updates only this island and never disturbs the
 * persisted-alert surfaces (KPIs, queue, intelligence, history).
 */
export const LiveNowBand = memo(function LiveNowBand() {
  const liveEvents = useLiveEvents();
  const { connectionStatus } = useLiveData();
  const events = Array.isArray(liveEvents) ? liveEvents : [];
  const connected = connectionStatus === 'live';

  return (
    <div style={{ border: '1px solid var(--color-red)', borderRadius: 12, overflow: 'hidden' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '10px 16px',
          background: 'var(--color-red-bg)',
          borderBottom: '1px solid var(--color-red)',
        }}
      >
        {connected && (
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'var(--color-red)',
              flexShrink: 0,
              animation: 'pulse-dot-red 2s ease-out infinite',
            }}
          />
        )}
        <Radio size={14} style={{ color: 'var(--color-red)', flexShrink: 0 }} />
        <span
          style={{
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: '0.05em',
            color: 'var(--color-red)',
            textTransform: 'uppercase',
          }}
        >
          Live Now
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
          {connected
            ? 'Driving events reported by the fleet'
            : 'Live events — disconnected'}
        </span>
      </div>

      <div
        style={{
          padding: '12px 16px',
          background: 'var(--color-surface)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: 6,
        }}
      >
        {events.length === 0 ? (
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
            No live driving events reported by the fleet right now.
          </span>
        ) : (
          events.map((event) => (
            <span
              key={event.id}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                padding: '4px 9px',
                borderRadius: 8,
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border-light)',
                fontSize: 11,
                color: 'var(--color-text-secondary)',
                lineHeight: 1,
              }}
            >
              <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                {event.vehicle_name}
              </span>
              {event.driver_name && (
                <span style={{ color: 'var(--color-text-muted)' }}>· {event.driver_name}</span>
              )}
              <span style={{ color: 'var(--color-red)', fontWeight: 600 }}>{event.label}</span>
            </span>
          ))
        )}
      </div>
    </div>
  );
});
