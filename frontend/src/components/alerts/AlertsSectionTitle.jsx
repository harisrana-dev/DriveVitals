import { memo } from 'react';

export const AlertsSectionTitle = memo(function AlertsSectionTitle({ title, subtitle, right }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, minWidth: 0 }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          {title}
        </span>
        {subtitle && (
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{subtitle}</span>
        )}
      </div>
      {right}
    </div>
  );
});
