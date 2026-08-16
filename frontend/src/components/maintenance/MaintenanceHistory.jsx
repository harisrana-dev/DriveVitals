import { memo } from 'react';
import { History } from 'lucide-react';

const GRID = '1.3fr 1.4fr 1.1fr 1.2fr 1fr';

function formatCompleted(iso) {
  if (!iso) return '\u2014';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '\u2014';
  return `${d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}

/**
 * Service history: real completed maintenance records, newest first. This
 * is authoritative backend data — no projected dates, no estimates.
 */
export const MaintenanceHistory = memo(function MaintenanceHistory({ history, onOpenVehicle }) {
  const list = Array.isArray(history) ? history : [];
  if (list.length === 0) return null;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <History size={14} style={{ color: 'var(--color-text-muted)' }} />
        <div>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Service History
          </span>
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 8 }}>
            {list.length} completed {list.length === 1 ? 'record' : 'records'} · real data only
          </span>
        </div>
      </div>

      <div style={{ border: '1px solid var(--color-border)', borderRadius: 10, overflow: 'hidden' }}>
        <div style={{ maxHeight: 300, overflowY: 'auto', scrollbarGutter: 'stable' }}>
          <div
            style={{
              position: 'sticky',
              top: 0,
              zIndex: 2,
              display: 'grid',
              gridTemplateColumns: GRID,
              gap: 10,
              padding: '10px 12px 8px',
              fontSize: 10,
              fontWeight: 600,
              color: 'var(--color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              background: 'var(--color-surface)',
              borderBottom: '1px solid var(--color-border)',
            }}
          >
            <span>Vehicle</span>
            <span>Service</span>
            <span>Component</span>
            <span>Completed</span>
            <span style={{ textAlign: 'right' }}>Odometer</span>
          </div>

          {list.map((h) => (
            <div
              key={h.id || `${h.vehicle_id}-${h.maintenance_type}-${h.completed_at}`}
              role={onOpenVehicle ? 'button' : undefined}
              tabIndex={onOpenVehicle ? 0 : undefined}
              onClick={() => onOpenVehicle && onOpenVehicle(h.vehicle_id)}
              onKeyDown={(e) => {
                if (onOpenVehicle && (e.key === 'Enter' || e.key === ' ')) {
                  e.preventDefault();
                  onOpenVehicle(h.vehicle_id);
                }
              }}
              style={{
                display: 'grid',
                gridTemplateColumns: GRID,
                gap: 10,
                alignItems: 'center',
                padding: '9px 12px',
                borderBottom: '1px solid var(--color-border-light)',
                cursor: onOpenVehicle ? 'pointer' : 'default',
                transition: 'background-color 0.12s ease',
              }}
              onMouseEnter={(e) => { if (onOpenVehicle) e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
              onMouseLeave={(e) => { if (onOpenVehicle) e.currentTarget.style.background = 'transparent'; }}
            >
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {h.vehicle_name}
              </span>
              <span style={{ fontSize: 12, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {h.maintenanceTypeLabel}
              </span>
              <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {h.component || '\u2014'}
              </span>
              <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', fontVariantNumeric: 'tabular-nums' }}>
                {formatCompleted(h.completed_at)}
              </span>
              <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', fontVariantNumeric: 'tabular-nums', textAlign: 'right' }}>
                {h.completed_odometer_km != null ? `${h.completed_odometer_km.toLocaleString()} km` : '\u2014'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});
