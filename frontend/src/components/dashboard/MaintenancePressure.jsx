import { memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Wrench } from 'lucide-react';
import { useDashboard } from '../../hooks/useDashboard';

const GRID = '1.4fr 1fr 62px 62px 1.2fr 1.2fr';

const LEVEL_META = {
  critical: { label: 'Critical', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  high: { label: 'High', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  medium: { label: 'Medium', color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
  good: { label: 'Good', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
};

/**
 * Maintenance pressure across the fleet: vehicles with actionable service
 * (overdue / due-soon / scheduled) and their nearest work item. Built from
 * the canonical maintenance work items — no estimated service history.
 * Rows deep-link to the Maintenance page for the vehicle.
 */
export const MaintenancePressure = memo(function MaintenancePressure() {
  const { maintenancePressure } = useDashboard();
  const navigate = useNavigate();
  const rows = Array.isArray(maintenancePressure) ? maintenancePressure : [];

  return (
    <div
      className="fade-in"
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
        minWidth: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
        <Wrench size={14} style={{ color: 'var(--color-amber)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          Maintenance Pressure
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 4 }}>
          {rows.length} {rows.length === 1 ? 'vehicle' : 'vehicles'} due
        </span>
      </div>
      <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 10 }}>
        Vehicles with service due (overdue / due-soon / scheduled)
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: GRID,
          gap: 8,
          padding: '0 4px 6px',
          fontSize: 10,
          fontWeight: 600,
          color: 'var(--color-text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        <span>Vehicle</span>
        <span>Driver</span>
        <span style={{ textAlign: 'right' }}>Overdue</span>
        <span style={{ textAlign: 'right' }}>Due soon</span>
        <span>Next service</span>
        <span>Due</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {rows.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 4px' }}>
            No vehicles currently have service due.
          </div>
        ) : (
          rows.slice(0, 6).map((row) => (
            <PressureRow
              key={row.vehicle_id}
              row={row}
              onOpen={() =>
                navigate(`/maintenance?vehicle=${encodeURIComponent(row.vehicle_id)}`)
              }
            />
          ))
        )}
      </div>
    </div>
  );
});

function PressureRow({ row, onOpen }) {
  const meta = LEVEL_META[row.level] || LEVEL_META.good;

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`Open maintenance for ${row.vehicle_name}`}
      className="row-focusable"
      onClick={onOpen}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && onOpen) {
          e.preventDefault();
          onOpen();
        }
      }}
      style={{
        display: 'grid',
        gridTemplateColumns: GRID,
        gap: 8,
        alignItems: 'center',
        padding: '7px 4px',
        borderRadius: 8,
        cursor: 'pointer',
        transition: 'background-color 0.12s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      <span style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
        <span
          style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: meta.color,
            flexShrink: 0,
          }}
        />
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {row.vehicle_name}
        </span>
      </span>
      <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {row.driver_name || '—'}
      </span>
      <span style={{ fontSize: 11, fontWeight: 600, textAlign: 'right', color: row.overdue > 0 ? 'var(--color-red)' : 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
        {row.overdue}
      </span>
      <span style={{ fontSize: 11, textAlign: 'right', color: row.dueSoon > 0 ? 'var(--color-amber)' : 'var(--color-text-muted)', fontWeight: row.dueSoon > 0 ? 600 : 400, fontVariantNumeric: 'tabular-nums' }}>
        {row.dueSoon}
      </span>
      <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {row.serviceLabel || '\u2014'}
      </span>
      <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {row.dueLabel || '\u2014'}
      </span>
    </div>
  );
}
