import { memo } from 'react';
import { RefreshCw } from 'lucide-react';
import { useLiveData } from '../../context/LiveDataContext';
import { useMaintenance } from '../../hooks/useMaintenance';

const CONNECTION_META = {
  live: { label: 'Live', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  connecting: { label: 'Connecting', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  offline: { label: 'Offline', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  syncing: { label: 'Syncing', color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
};

const STALE_AFTER_MS = 15 * 60 * 1000;

function formatClock(ts) {
  if (!ts) return null;
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

/**
 * Command header. Maintenance is a REST snapshot (hydrated once), so the
 * header always shows the truthful last-synced time instead of claiming a
 * live maintenance stream; the connection chip reflects the overall fleet
 * connection state and the sync label shows when maintenance data was last
 * refreshed. Stale data is labelled as such.
 */
export const MaintenanceCommandHeader = memo(function MaintenanceCommandHeader() {
  const { connectionStatus, maintenanceSyncedAt, syncing, sync } = useLiveData();
  const { kpis } = useMaintenance();
  const meta = CONNECTION_META[connectionStatus] || CONNECTION_META.offline;
  const syncedAt = formatClock(maintenanceSyncedAt);
  const isStale =
    maintenanceSyncedAt != null && Date.now() - maintenanceSyncedAt > STALE_AFTER_MS;

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
          Maintenance
        </h1>
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>
          Fleet service planning and readiness
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
            {kpis.total}
          </span>
          work items
          <span style={{ marginLeft: 6, color: 'var(--color-text-muted)' }}>
            · {kpis.vehiclesRequiringService} {kpis.vehiclesRequiringService === 1 ? 'vehicle' : 'vehicles'}
          </span>
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

        {syncedAt && (
          <span
            style={{
              fontSize: 11,
              color: isStale ? 'var(--color-amber)' : 'var(--color-text-muted)',
              fontWeight: isStale ? 600 : 400,
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {isStale ? 'Maintenance data last synced' : 'Synced'} {syncedAt}
            {isStale ? ' · outdated' : ''}
          </span>
        )}

        <button
          onClick={() => sync()}
          disabled={syncing}
          title="Refresh maintenance data"
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
