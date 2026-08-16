import { memo } from 'react';

const TABS = [
  { key: 'overdue', label: 'Overdue' },
  { key: 'dueSoon', label: 'Due Soon' },
  { key: 'scheduled', label: 'Scheduled' },
  { key: 'future', label: 'Future' },
  { key: 'all', label: 'All' },
];

export const MaintenanceStatusTabs = memo(function MaintenanceStatusTabs({ counts, activeTab, onTabChange }) {
  return (
    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
      {TABS.map((t) => {
        const active = activeTab === t.key;
        return (
          <button
            key={t.key}
            onClick={() => onTabChange(t.key)}
            aria-pressed={active}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '5px 12px',
              borderRadius: 8,
              border: `1px solid ${active ? 'var(--color-accent)' : 'var(--color-border)'}`,
              background: active ? 'var(--color-accent-subtle)' : 'transparent',
              color: active ? 'var(--color-accent)' : 'var(--color-text-secondary)',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'inherit',
              transition: 'all 0.12s ease',
              lineHeight: 1,
            }}
          >
            {t.label}
            <span
              style={{
                fontSize: 10,
                fontWeight: 700,
                padding: '1px 6px',
                borderRadius: 8,
                background: active ? 'var(--color-accent)' : 'var(--color-surface-hover)',
                color: active ? '#fff' : 'var(--color-text-muted)',
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {counts[t.key]}
            </span>
          </button>
        );
      })}
    </div>
  );
});
