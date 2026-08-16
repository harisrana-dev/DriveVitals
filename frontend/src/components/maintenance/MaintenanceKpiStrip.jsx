import { memo } from 'react';

const KPI_DEFS = [
  { key: 'overdue', label: 'Overdue', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  { key: 'dueSoon', label: 'Due Soon', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  { key: 'dueWithin2000', label: 'Due Within 2,000 km', color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
  { key: 'vehiclesRequiringService', label: 'Vehicles Requiring Service', color: 'var(--color-accent)', bg: 'var(--color-accent-subtle)' },
];

/**
 * KPI strip. Every figure is a canonical count from the grouped work items
 * (Overdue, Due Soon, Due Within 2,000 km — distinct work items, Vehicles
 * Requiring Service — distinct vehicles). Clicking a card lifts the
 * matching population to the work queue.
 */
export const MaintenanceKpiStrip = memo(function MaintenanceKpiStrip({ kpis, activeKey, onSelect }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(148px, 1fr))', gap: 10 }}>
      {KPI_DEFS.map((def) => {
        const isActive = activeKey === def.key;
        return (
          <button
            key={def.key}
            onClick={() => onSelect(def.key)}
            aria-pressed={isActive}
            title={`View ${def.label.toLowerCase()} work items`}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
              padding: '12px 14px',
              borderRadius: 12,
              background: isActive ? def.bg : 'var(--color-surface)',
              border: `1px solid ${isActive ? def.color : 'var(--color-border)'}`,
              cursor: 'pointer',
              textAlign: 'left',
              fontFamily: 'inherit',
              transition: 'all 0.15s ease',
            }}
          >
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontSize: 11,
                fontWeight: 600,
                color: 'var(--color-text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: def.color, flexShrink: 0 }} />
              {def.label}
            </span>
            <span
              style={{
                fontSize: 26,
                fontWeight: 700,
                color: 'var(--color-text-primary)',
                fontVariantNumeric: 'tabular-nums',
                lineHeight: 1,
              }}
            >
              {kpis[def.key]}
            </span>
          </button>
        );
      })}
    </div>
  );
});
