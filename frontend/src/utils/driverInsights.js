/**
 * Deterministic, rule-based driver insights.
 *
 * Every insight is generated from real recorded data only (driver
 * statistics, completed-trip scores, fleet comparisons). The
 * Observation -> Evidence -> Implication -> Action structure keeps the
 * reasoning auditable. When the data does not support an insight, no
 * insight is emitted — an explicit "no data" card is used instead.
 */

import { computeDriverTrend } from './driverTrend';
import { driverRiskLevel } from '../services/driverAdapter';

const EVENT_LABELS = {
  overspeed: 'Overspeed',
  harshBraking: 'Harsh braking',
  aggressiveAcceleration: 'Aggressive throttle',
  highRpm: 'High RPM',
};

function capitalize(value) {
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function generateDriverInsights({ driver, allDrivers }) {
  if (!driver) return [];

  const insights = [];
  const scored = (allDrivers || []).filter(
    (d) => d && d.historical?.safetyScore != null
  );
  const historical = driver.historical || {};
  const riskLevel = driverRiskLevel(driver);

  if (historical.tripsCompleted === 0) {
    insights.push({
      id: 'no-trips',
      category: 'activity',
      severity: 'info',
      title: 'No completed trips recorded',
      observation: `${driver.name} has no completed trips on record yet.`,
      evidence: 'From recorded trip history.',
      implication: 'Safety, behaviour and efficiency metrics populate as trips are completed.',
      action: 'Assign a route to this driver to start collecting telemetry.',
    });
    return insights;
  }

  if (historical.safetyScore != null && scored.length >= 3) {
    const fleetAvg = scored.reduce((s, d) => s + d.historical.safetyScore, 0) / scored.length;
    const diff = Math.round(historical.safetyScore - fleetAvg);
    const below = diff < 0;
    insights.push({
      id: 'fleet-benchmark',
      category: 'benchmark',
      severity: below ? (diff <= -10 ? 'critical' : 'high') : 'info',
      title: below ? 'Below fleet-average safety' : 'Above fleet-average safety',
      observation: `${driver.name}'s safety score of ${Math.round(
        historical.safetyScore
      )} is ${Math.abs(diff)} point${Math.abs(diff) === 1 ? '' : 's'} ${
        below ? 'below' : 'above'
      } the fleet average of ${Math.round(fleetAvg)}.`,
      evidence: `Compared across ${scored.length} scored drivers.`,
      implication: below
        ? 'This driver contributes above-average safety risk relative to the fleet.'
        : 'This driver is a positive safety reference for the fleet.',
      action: below
        ? 'Prioritise a coaching session focused on this driver\u2019s leading behaviour events.'
        : 'Consider highlighting this driver\u2019s practices in fleet training.',
    });
  }

  const eventTypes = [
    { key: 'overspeed', count: driver.behaviour.overspeedEvents.count },
    { key: 'harshBraking', count: driver.behaviour.harshBraking.count },
    { key: 'aggressiveAcceleration', count: driver.behaviour.aggressiveAcceleration.count },
    { key: 'highRpm', count: driver.behaviour.highRpmEvents.count },
  ];
  const totalEvents = driver.behaviour.totalEvents;

  if (totalEvents > 0) {
    const worst = eventTypes.reduce((a, b) => (b.count > a.count ? b : a), eventTypes[0]);
    const label = EVENT_LABELS[worst.key];
    insights.push({
      id: 'leading-behaviour',
      category: 'behaviour',
      severity: riskLevel === 'critical' ? 'critical' : 'high',
      title: `${label} is the leading behaviour event`,
      observation: `${label} accounts for ${worst.count} of ${totalEvents} recorded behaviour event${
        totalEvents === 1 ? '' : 's'
      }.`,
      evidence: 'From the driver\u2019s recorded behaviour event history.',
      implication:
        worst.count >= 5
          ? 'Repeated instances suggest a persistent driving pattern rather than a one-off lapse.'
          : 'Frequent enough to warrant targeted feedback.',
      action:
        worst.key === 'overspeed'
          ? 'Review speed compliance on this driver\u2019s typical routes.'
          : `Coach on avoiding ${label.toLowerCase()} events.`,
    });
  }

  const overspeedShare =
    totalEvents > 0 ? driver.behaviour.overspeedEvents.count / totalEvents : 0;
  if (overspeedShare >= 0.5) {
    insights.push({
      id: 'overspeed-share',
      category: 'behaviour',
      severity: 'moderate',
      title: 'Most recorded events are speeding',
      observation: `${Math.round(overspeedShare * 100)}% of recorded behaviour events are speeding.`,
      evidence: 'From the driver\u2019s recorded behaviour event history.',
      implication: 'Route or schedule pressure may be pushing the driver to exceed limits.',
      action: 'Cross-check this driver\u2019s routes against achievable journey times.',
    });
  }

  const trend = computeDriverTrend(historical.performanceHistory);
  if (trend && trend.direction === 'declining') {
    insights.push({
      id: 'safety-trend',
      category: 'trend',
      severity: 'high',
      title: 'Safety score is declining',
      observation: `Average safety score has dropped by ${Math.abs(
        trend.delta
      )} points across the most recent completed trips.`,
      evidence: `Based on ${trend.observations} completed trips with recorded scores.`,
      implication: 'A sustained decline can indicate fatigue, distraction or route pressure.',
      action: 'Review recent trip scores and schedule a performance check-in.',
    });
  }

  if (trend && trend.direction === 'improving') {
    insights.push({
      id: 'safety-trend-up',
      category: 'trend',
      severity: 'info',
      title: 'Safety score is improving',
      observation: `Average safety score has increased by ${Math.abs(
        trend.delta
      )} points across the most recent completed trips.`,
      evidence: `Based on ${trend.observations} completed trips with recorded scores.`,
      implication: 'Recent behaviour changes appear to be having a positive effect.',
      action: 'Maintain the current approach; keep monitoring for regression.',
    });
  }

  const scoreKeys = ['safety', 'efficiency', 'aggression'];
  const missingScores = scoreKeys.filter(
    (key) => historical.scores[key] == null
  );
  if (missingScores.length > 0 && historical.tripsCompleted > 0) {
    insights.push({
      id: 'partial-scores',
      category: 'data',
      severity: 'info',
      title: 'Partial score data',
      observation: `${missingScores.map(capitalize).join(' and ')} score${
        missingScores.length === 1 ? ' is' : 's are'
      } not yet available for this driver.`,
      evidence: 'From persisted driver statistics.',
      implication: 'These scores will appear once the driver completes more trips.',
      action: 'No action needed; the metrics self-populate as trips are completed.',
    });
  }

  return insights;
}
