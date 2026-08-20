import { memo } from 'react';
import { useLiveData } from '../../context/useLiveData';
import { useAlerts } from '../../hooks/useAlerts';

const CONNECTION_META = {
  live: { label: 'Live', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  connecting: { label: 'Connecting', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  offline: { label: 'Offline', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  syncing: { label: 'Syncing', color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
};

function formatClock(ts) {
  if (!ts) return null;
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export const CommandHeader = memo(function CommandHeader() {
  const { alertsConnectionState, lastUpdate } = useLiveData();
  const { kpis } = useAlerts();
  const meta = CONNECTION_META[alertsConnectionState] || CONNECTION_META.offline;
  const syncTime = formatClock(lastUpdate);

  return (
    <div
      className="fade-in"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 16,
        flexWrap: 'wrap',
      }}
    >
      <div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: 'var(--color-text-primary)', letterSpacing: '-0.01em' }}>
          Alerts
        </h1>
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>
          Fleet incident monitoring and operational response
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '5px 10px',
            borderRadius: 8,
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            fontSize: 11,
            color: 'var(--color-text-secondary)',
            lineHeight: 1,
          }}
        >
          <span style={{ fontWeight: 700, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
            {kpis.active}
          </span>
          active
          {kpis.unacknowledged > 0 && (
            <span style={{ marginLeft: 6, color: 'var(--color-amber)', fontWeight: 600 }}>
              · {kpis.unacknowledged} require attention
            </span>
          )}
        </div>

        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '5px 10px',
            borderRadius: 8,
            background: meta.bg,
            border: `1px solid ${meta.color}`,
            fontSize: 11,
            fontWeight: 700,
            color: meta.color,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            lineHeight: 1,
          }}
        >
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: meta.color, flexShrink: 0 }} />
          {meta.label}
        </div>

        {syncTime && (
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
            Last sync {syncTime}
          </span>
        )}
      </div>
    </div>
  );
});
