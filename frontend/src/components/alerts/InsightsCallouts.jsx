import { memo } from 'react';
import { Sparkles } from 'lucide-react';

const KIND_STYLE = {
  ATTENTION: { color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  RISK: { color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  INSIGHT: { color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
  STALE: { color: 'var(--color-text-muted)', bg: 'var(--color-surface-hover)' },
  'DATA QUALITY': { color: 'var(--color-text-muted)', bg: 'var(--color-surface-hover)' },
};

/**
 * Derived-only operational callouts. Each insight is emitted only when
 * its backing fact exists in the data (see `computeInsights`) — nothing
 * here is fabricated.
 */
export const InsightsCallouts = memo(function InsightsCallouts({ insights }) {
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
        const st = KIND_STYLE[item.kind] || KIND_STYLE.INSIGHT;
        return (
          <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
            <span
              style={{
                padding: '2px 8px',
                borderRadius: 6,
                background: st.bg,
                color: st.color,
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: '0.04em',
                flexShrink: 0,
              }}
            >
              {item.kind}
            </span>
            <span style={{ color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>{item.text}</span>
          </div>
        );
      })}
    </div>
  );
});
