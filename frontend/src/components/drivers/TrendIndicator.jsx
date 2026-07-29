import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const CONFIG = {
  up: {
    Icon: TrendingUp,
    color: 'var(--color-green)',
    label: 'Improving',
  },
  down: {
    Icon: TrendingDown,
    color: 'var(--color-red)',
    label: 'Declining',
  },
  warning: {
    Icon: TrendingDown,
    color: 'var(--color-amber)',
    label: 'Requires attention',
  },
  stable: {
    Icon: Minus,
    color: 'var(--color-text-muted)',
    label: 'Stable',
  },
};

export function TrendIndicator({ trend, showPercent, showLabel, size, compact }) {
  if (!trend) return null;

  const cfg = CONFIG[trend.direction] || CONFIG.stable;
  const Icon = cfg.Icon;
  const iconSize = size || (compact ? 12 : 14);
  const textSize = compact ? 10 : 11;

  if (compact && trend.direction === 'stable') return null;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 3,
        color: cfg.color,
        fontWeight: 600,
        fontSize: textSize,
        lineHeight: 1,
        fontVariantNumeric: 'tabular-nums',
        whiteSpace: 'nowrap',
      }}
      title={cfg.label}
    >
      <Icon size={iconSize} strokeWidth={2} style={{ flexShrink: 0 }} />
      {showPercent && trend.direction !== 'stable' && (
        <span>{trend.direction === 'up' ? '+' : ''}{trend.pct}%</span>
      )}
      {showLabel && (
        <span>{cfg.label}</span>
      )}
    </span>
  );
}
