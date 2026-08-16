import { memo } from 'react';
import { CalendarRange } from 'lucide-react';

const BUCKET_COLOR = {
  overdue: 'var(--color-red)',
  week: 'var(--color-amber)',
  twoWeeks: 'var(--color-blue)',
  month: 'var(--color-accent)',
  later: 'var(--color-green)',
};

/**
 * Scheduled-due horizon. Built only from work items that carry a real
 * due_date (see computeMaintenanceHorizon); the panel hides itself when no
 * dates exist rather than drawing an invented schedule. Coverage shows how
 * many items had a scheduled date at all.
 */
export const MaintenanceHorizonPanel = memo(function MaintenanceHorizonPanel({ horizon, onOpenAll }) {
  if (!horizon) return null;
  const maxCount = Math.max(...horizon.buckets.map((b) => b.count), 1);

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <CalendarRange size={14} style={{ color: 'var(--color-accent)' }} />
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Scheduled-Due Horizon
          </span>
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 4 }}>
            {horizon.total} dated · {Math.round(horizon.coverage * 100)}% of work items
          </span>
        </div>
        {onOpenAll && (
          <button
            onClick={onOpenAll}
            style={{
              padding: '4px 10px',
              borderRadius: 6,
              border: '1px solid var(--color-border)',
              background: 'transparent',
              color: 'var(--color-text-secondary)',
              fontSize: 10,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'inherit',
              lineHeight: 1,
              transition: 'all 0.12s ease',
            }}
          >
            View queue
          </button>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {horizon.buckets.map((b) => (
          <div key={b.key} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ width: 110, fontSize: 11, color: 'var(--color-text-secondary)', flexShrink: 0 }}>
              {b.label}
            </span>
            <div style={{ flex: 1, height: 8, borderRadius: 4, background: 'var(--color-border-light)', overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  width: `${(b.count / maxCount) * 100}%`,
                  background: BUCKET_COLOR[b.key] || 'var(--color-accent)',
                  borderRadius: 4,
                  transition: 'width 0.25s ease',
                }}
              />
            </div>
            <span style={{ width: 24, fontSize: 11, fontWeight: 700, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums', textAlign: 'right', flexShrink: 0 }}>
              {b.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
});
