import { memo } from 'react';
import { Sparkles } from 'lucide-react';

const KIND_STYLE = {
  warning: { color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  info: { color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
};

/**
 * Derived-only operational callouts. Each insight is emitted only when its
 * backing fact exists in the data (see computeMaintenanceInsights) —
 * nothing here is fabricated.
 */
export const MaintenanceInsights = memo(function MaintenanceInsights({ insights }) {
  if (!Array.isArray(insights) || insights.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          fontSize: 11,
          fontWeight: 600,
          color: 'var(--color-text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}
      >
        <Sparkles size={12} />
        Operational Insights
      </div>
      {insights.map((item, idx) => {
        const st = KIND_STYLE[item.kind] || KIND_STYLE.info;
        return (
          <div
            key={`${item.key}-${idx}`}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 8,
              fontSize: 12,
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border-light)',
              borderRadius: 10,
              padding: '10px 12px',
            }}
          >
            <span
              style={{
                padding: '2px 8px',
                borderRadius: 6,
                background: st.bg,
                color: st.color,
                fontSize: 10,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                flexShrink: 0,
                marginTop: 1,
              }}
            >
              {item.kind === 'warning' ? 'Attention' : 'Insight'}
            </span>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', lineHeight: 1.4 }}>
                {item.title}
              </div>
              <div style={{ color: 'var(--color-text-secondary)', lineHeight: 1.4, marginTop: 2 }}>
                {item.body}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
});
