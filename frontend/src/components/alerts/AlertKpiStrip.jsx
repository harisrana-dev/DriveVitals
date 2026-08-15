import { memo } from 'react';

const KPI_DEFS = [
  { key: 'critical', label: 'Critical', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  { key: 'high', label: 'High', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  { key: 'unacknowledged', label: 'Unacknowledged', color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
  { key: 'active', label: 'Active', color: 'var(--color-accent)', bg: 'var(--color-accent-subtle)' },
  { key: 'resolved24h', label: 'Resolved (24h)', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
];

/**
 * One KPI strip, five live counts. Every value is a canonical count of
 * backend alert rows (see `computeAlertKpis`); the resolved figure is the
 * subset resolved within the last 24h. Clicking a card filters the
 * history table to that population.
 */
export const AlertKpiStrip = memo(function AlertKpiStrip({ kpis, activeKey, onSelect }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(148px, 1fr))', gap: 10 }}>
      {KPI_DEFS.map((def) => {
        const isActive = activeKey === def.key;
        return (
          <button
            key={def.key}
            onClick={() => onSelect(def.key)}
            aria-pressed={isActive}
            title={`View ${def.label.toLowerCase()} alerts`}
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
