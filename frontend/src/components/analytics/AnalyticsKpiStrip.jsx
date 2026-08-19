import { memo } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const KPI_ICONS = {
  up: TrendingUp,
  down: TrendingDown,
  flat: Minus,
};

const KPI_COLORS = {
  'Safety Score': { color: 'var(--color-accent)', bg: 'var(--color-accent-subtle)' },
  'Completed Trips': { color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
  'Fleet Fuel Efficiency': { color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  'Safety Events': { color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  'Vehicle Health': { color: 'var(--color-purple, #8b5cf6)', bg: 'rgba(139,92,246,0.08)' },
};

function TrendBadge({ change_pct, change_direction }) {
  if (change_pct == null || change_direction == null) return null;
  const Icon = KPI_ICONS[change_direction] || Minus;
  const isUp = change_direction === 'up';
  const isDown = change_direction === 'down';
  const color = isUp ? 'var(--color-green)' : isDown ? 'var(--color-red)' : 'var(--color-text-muted)';

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 3,
      fontSize: 11,
      fontWeight: 600,
      color,
    }}>
      <Icon size={12} strokeWidth={2} />
      {isUp ? '↑' : isDown ? '↓' : '—'} {Math.abs(change_pct).toFixed(1)}%
    </span>
  );
}

export const AnalyticsKpiStrip = memo(function AnalyticsKpiStrip({ kpis }) {
  if (!kpis || kpis.length === 0) return null;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
      {kpis.map((kpi) => {
        const palette = KPI_COLORS[kpi.label] || { color: 'var(--color-text-secondary)', bg: 'var(--color-surface)' };
        return (
          <div
            key={kpi.label}
            style={{
              padding: '14px 16px',
              borderRadius: 12,
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              marginBottom: 8,
            }}>
              <span style={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                background: palette.color,
                flexShrink: 0,
              }} />
              <span style={{
                fontSize: 11,
                fontWeight: 600,
                color: 'var(--color-text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}>
                {kpi.label}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{
                fontSize: 26,
                fontWeight: 700,
                color: 'var(--color-text-primary)',
                lineHeight: 1.1,
              }}>
                {kpi.value != null ? kpi.value : '—'}
              </span>
              {kpi.unit && (
                <span style={{ fontSize: 12, color: 'var(--color-text-muted)', fontWeight: 500 }}>
                  {kpi.unit}
                </span>
              )}
            </div>
            <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
              <TrendBadge change_pct={kpi.change_pct} change_direction={kpi.change_direction} />
              {kpi.context && (
                <span style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>
                  {kpi.context}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
});
