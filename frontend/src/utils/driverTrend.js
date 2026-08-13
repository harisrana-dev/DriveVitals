/**
 * Real, evidence-based driver trend computation.
 *
 * Trends are derived exclusively from a driver's recorded completed-trip
 * safety scores (chronological). A trend is only reported once a
 * minimum number of observations exists; a single good or bad trip is
 * never presented as a trend.
 */

export const TREND_MIN_OBSERVATIONS = 4;
export const TREND_RECENT_COUNT = 3;
export const TREND_DELTA_THRESHOLD = 2;

export function classifyTrend(delta) {
  if (delta > TREND_DELTA_THRESHOLD) return 'improving';
  if (delta < -TREND_DELTA_THRESHOLD) return 'declining';
  return 'stable';
}

/**
 * Compute a driver's safety trend from completed-trip scores.
 *
 * @param {Array<{score: number, completedAt?: string}>} scores
 *        Completed-trip scores, chronological or unordered (sorted here).
 * @param {{ minObservations?: number, recentCount?: number }} [options]
 * @returns {{
 *   direction: 'improving'|'declining'|'stable',
 *   delta: number,
 *   pct: number,
 *   observations: number,
 *   recentAvg: number,
 *   previousAvg: number,
 * } | null} null when there are not enough scored trips to compute a
 * meaningful trend.
 */
export function computeDriverTrend(scores, options = {}) {
  const minObservations = options.minObservations ?? TREND_MIN_OBSERVATIONS;
  const recentCount = options.recentCount ?? TREND_RECENT_COUNT;

  const valid = (scores || [])
    .filter((s) => s && s.score != null)
    .map((s) => ({ score: s.score, at: s.completedAt || 0 }))
    .sort((a, b) => new Date(a.at) - new Date(b.at));

  if (valid.length < minObservations) return null;

  const recent = valid.slice(-recentCount);
  const previous = valid.slice(-recentCount * 2, -recentCount);
  if (previous.length === 0) return null;

  const avg = (items) => items.reduce((sum, item) => sum + item.score, 0) / items.length;
  const recentAvg = avg(recent);
  const previousAvg = avg(previous);

  const delta = Math.round((recentAvg - previousAvg) * 10) / 10;
  const pct = previousAvg > 0 ? Math.round((delta / previousAvg) * 100) : 0;

  return {
    direction: classifyTrend(delta),
    delta,
    pct: Math.abs(pct),
    observations: valid.length,
    recentAvg,
    previousAvg,
  };
}
