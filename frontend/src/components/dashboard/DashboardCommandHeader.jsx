import { memo } from 'react';
import { RefreshCw, Activity } from 'lucide-react';
import { useDashboard } from '../../hooks/useDashboard';

const CONNECTION_META = {
  live: { label: 'Live', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  connecting: { label: 'Connecting', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  offline: { label: 'Offline', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  syncing: { label: 'Syncing', color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
  stale: { label: 'Stale', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
};

function formatClock(ts) {
  if (!ts) return null;
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

/**
 * Command header for the dashboard. The connection chip reflects the
 * derived fleet state (live / connecting / syncing / offline / stale) and
 * the last-sync time comes from the real snapshot timestamp — the header
 * never claims live data the socket does not have.
 */
export const DashboardCommandHeader = memo(function DashboardCommandHeader() {
  const { connState, activeNow, totalFleet, lastUpdate, syncing, sync } = useDashboard();
  const meta = CONNECTION_META[connState] || CONNECTION_META.offline;
  const syncTime = formatClock(lastUpdate);
  const hasLiveData = activeNow != null;

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
          Dashboard
        </h1>
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>
          Fleet command center
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
          <Activity size={12} style={{ color: hasLiveData ? 'var(--color-green)' : 'var(--color-text-muted)' }} />
          {hasLiveData ? (
            <>
              <span style={{ fontWeight: 700, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
                {activeNow}
              </span>
              active
              <span style={{ marginLeft: 6, color: 'var(--color-text-muted)' }}>
                · {totalFleet} fleet
              </span>
            </>
          ) : (
            <span style={{ color: 'var(--color-text-muted)' }}>Live data unavailable</span>
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

        <button
          onClick={() => sync()}
          disabled={syncing}
          title="Reconnect and refresh data"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            padding: '5px 10px',
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-secondary)',
            fontSize: 11,
            fontWeight: 500,
            cursor: 'pointer',
            fontFamily: 'inherit',
            lineHeight: 1,
            transition: 'all 0.12s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-surface-hover)';
            e.currentTarget.style.color = 'var(--color-text-primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--color-surface)';
            e.currentTarget.style.color = 'var(--color-text-secondary)';
          }}
        >
          <RefreshCw size={12} style={syncing ? { animation: 'spin 1s linear infinite' } : undefined} />
          {syncing ? 'Refreshing' : 'Refresh'}
        </button>
      </div>
    </div>
  );
});
