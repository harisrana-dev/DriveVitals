import { memo } from 'react';
import { Radio, RefreshCw } from 'lucide-react';
import { useFleetContext } from '../../context/FleetContext';
import { MaintenanceKpiCards } from './MaintenanceKpiCards';

export const MaintenanceOverview = memo(function MaintenanceOverview() {
  const { dashboard } = useFleetContext();
  const isLive = !!dashboard?.vehicles?.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              marginBottom: 4,
            }}
          >
            Maintenance
          </h1>
          <p
            style={{
              fontSize: 13,
              color: 'var(--color-text-secondary)',
            }}
          >
            Fleet maintenance planning and service operations
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--color-text-muted)' }}>
            <Radio size={13} style={{ color: isLive ? 'var(--color-green)' : 'var(--color-text-muted)' }} />
            <span>{isLive ? 'Live' : 'Offline'}</span>
          </div>
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            {isLive ? 'Updated just now' : 'Connecting...'}
          </span>
          <button
            aria-label="Refresh data"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 32,
              height: 32,
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
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
            <RefreshCw size={15} strokeWidth={1.8} />
          </button>
        </div>
      </div>
      <MaintenanceKpiCards />
    </div>
  );
});
