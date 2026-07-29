import { memo } from 'react';
import { useAlerts } from '../../hooks/useAlerts';

const CATEGORY_COLORS = {
  Driving: 'var(--color-red)',
  Engine: 'var(--color-amber)',
  Fuel: 'var(--color-green)',
  Cooling: 'var(--color-accent)',
  Electrical: 'var(--color-text-muted)',
};

export const AlertDistribution = memo(function AlertDistribution() {
  const { categoryDist } = useAlerts();
  const maxCount = Math.max(...categoryDist.map((c) => c.count), 1);

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
        flex: 1,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 14 }}>
        Alert Distribution
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {categoryDist.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            No distribution data.
          </div>
        ) : (
          categoryDist.map((item) => {
            const color = CATEGORY_COLORS[item.category] || 'var(--color-text-muted)';
            const widthPct = (item.count / maxCount) * 100;
            return (
              <div key={item.category} style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                  <span style={{ color: 'var(--color-text-secondary)', fontWeight: 500 }}>{item.category}</span>
                  <span style={{ color: 'var(--color-text-primary)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                    {item.count} · {item.pct}%
                  </span>
                </div>
                <div
                  style={{
                    width: '100%',
                    height: 8,
                    borderRadius: 4,
                    background: 'var(--color-border-light)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${widthPct}%`,
                      height: '100%',
                      borderRadius: 4,
                      background: color,
                      transition: 'width 0.5s ease, background-color 0.3s ease',
                    }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
});
