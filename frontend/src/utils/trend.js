import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export function computeTrend(current, previous) {
  if (previous == null) return null;

  const delta = current - previous;
  const pct = previous > 0 ? Math.round((delta / previous) * 100) : 0;

  if (delta > 1) return { direction: 'up', delta, pct: Math.abs(pct) };
  if (delta < -1) return { direction: 'down', delta, pct: Math.abs(pct) };
  if (delta < 0) return { direction: 'warning', delta, pct: Math.abs(pct) };
  return { direction: 'stable', delta: 0, pct: 0 };
}

export function getDriverTrend(score) {
  if (score >= 90) {
    return { direction: 'up', Icon: TrendingUp, color: 'var(--color-green)' };
  }
  if (score >= 70) {
    return { direction: 'stable', Icon: Minus, color: 'var(--color-amber)' };
  }
  return { direction: 'down', Icon: TrendingDown, color: 'var(--color-red)' };
}
