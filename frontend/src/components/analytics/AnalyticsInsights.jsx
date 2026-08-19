import { memo } from 'react';
import { Lightbulb, TrendingUp, TrendingDown, Minus, AlertTriangle, Truck, Users, Fuel } from 'lucide-react';

const CATEGORY_ICONS = {
  trips: Truck,
  safety: AlertTriangle,
  fuel: Fuel,
  drivers: Users,
};

const CATEGORY_COLORS = {
  trips: 'var(--color-blue)',
  safety: 'var(--color-amber)',
  fuel: 'var(--color-green)',
  drivers: 'var(--color-accent)',
};

const CHANGE_ICONS = {
  up: TrendingUp,
  down: TrendingDown,
  flat: Minus,
};

export const AnalyticsInsights = memo(function AnalyticsInsights({ insights }) {
  const items = insights?.insights || [];

  if (items.length === 0) {
    return (
      <div>
        <h2 style={{
          fontSize: 14,
          fontWeight: 700,
          color: 'var(--color-text-primary)',
          marginBottom: 12,
          letterSpacing: '-0.01em',
        }}>
          Insights
        </h2>
        <div style={{
          padding: '32px 20px',
          borderRadius: 14,
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          color: 'var(--color-text-muted)',
          fontSize: 13,
          textAlign: 'center',
        }}>
          <Lightbulb size={24} style={{ color: 'var(--color-text-muted)', marginBottom: 8 }} />
          <div>Insufficient data for insights in this period</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 style={{
        fontSize: 14,
        fontWeight: 700,
        color: 'var(--color-text-primary)',
        marginBottom: 12,
        letterSpacing: '-0.01em',
      }}>
        Insights
      </h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {items.map((insight) => {
          const CatIcon = CATEGORY_ICONS[insight.category] || Lightbulb;
          const catColor = CATEGORY_COLORS[insight.category] || 'var(--color-text-muted)';
          const ChangeIcon = insight.change_direction ? CHANGE_ICONS[insight.change_direction] : null;

          return (
            <div
              key={insight.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 12,
                padding: '12px 16px',
                borderRadius: 12,
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div style={{
                width: 32,
                height: 32,
                borderRadius: 8,
                background: `${catColor}12`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}>
                <CatIcon size={15} style={{ color: catColor }} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  lineHeight: 1.3,
                  marginBottom: 2,
                }}>
                  {insight.title}
                </div>
                <div style={{
                  fontSize: 11,
                  color: 'var(--color-text-muted)',
                  lineHeight: 1.4,
                }}>
                  {insight.description}
                </div>
              </div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                flexShrink: 0,
              }}>
                {insight.metric_value && (
                  <span style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: 'var(--color-text-primary)',
                    padding: '3px 8px',
                    borderRadius: 6,
                    background: 'var(--color-surface-hover, rgba(0,0,0,0.03))',
                  }}>
                    {insight.metric_value}
                  </span>
                )}
                {ChangeIcon && insight.change_pct != null && (
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 2,
                    fontSize: 11,
                    fontWeight: 600,
                    color: insight.change_direction === 'up' ? 'var(--color-green)' : 'var(--color-red)',
                    padding: '3px 6px',
                    borderRadius: 6,
                    background: insight.change_direction === 'up' ? 'var(--color-green-bg)' : 'var(--color-red-bg)',
                  }}>
                    <ChangeIcon size={11} strokeWidth={2} />
                    {Math.abs(insight.change_pct).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});
