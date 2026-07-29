import { memo } from 'react';
import { useAlerts } from '../../hooks/useAlerts';
import { severityColor } from '../../utils/alerts';

export const AlertTimeline = memo(function AlertTimeline() {
  const { timeline } = useAlerts();

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
        Alert Timeline
      </div>
      <div
        style={{
          maxHeight: 320,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 0,
        }}
      >
        {timeline.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            No alert history available.
          </div>
        ) : (
          timeline.map((entry, i) => (
            <div
              key={entry.id || `tl-${i}`}
              style={{
                display: 'flex',
                gap: 12,
                padding: '8px 0',
                borderBottom: i < timeline.length - 1 ? '1px solid var(--color-border-light)' : 'none',
              }}
            >
              <div
                style={{
                  width: 2,
                  borderRadius: 1,
                  background: severityColor(entry.severity),
                  flexShrink: 0,
                }}
              />
              <div
                style={{
                  fontSize: 11,
                  color: 'var(--color-text-muted)',
                  fontVariantNumeric: 'tabular-nums',
                  minWidth: 60,
                  flexShrink: 0,
                }}
              >
                {new Date(entry.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, color: 'var(--color-text-primary)', fontWeight: 500 }}>
                  {entry.vehicle_name}
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                  {entry.eventType}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: severityColor(entry.severity),
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 600,
                    color: severityColor(entry.severity),
                    textTransform: 'uppercase',
                    letterSpacing: '0.03em',
                  }}
                >
                  {entry.severity}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
});
