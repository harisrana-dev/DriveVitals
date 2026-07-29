import { memo } from 'react';
import { useSmoothValue } from '../../hooks/useSmoothValue';

const THRESHOLDS = [
  { min: 95, color: '#22C55E', label: 'Healthy' },
  { min: 80, color: '#86EFAC', label: 'Normal' },
  { min: 65, color: '#FACC15', label: 'Minor Stress' },
  { min: 45, color: '#FB923C', label: 'High Stress' },
  { min: 0, color: '#EF4444', label: 'Critical' },
];

function getHealthColor(score) {
  for (const t of THRESHOLDS) {
    if (score >= t.min) return t.color;
  }
  return '#EF4444';
}

function getHealthLabel(vehicle) {
  const { activeAlert, alertCount, rpm, activeEventTypes } = vehicle;
  const events = activeEventTypes || [];

  if (events.length > 1) return 'Multiple Active Events';

  if (events.length === 1) {
    const evt = events[0];
    if (evt === 'high_rpm') return 'High RPM';
    if (evt === 'harsh_braking') return 'Brake Stress';
    if (evt === 'aggressive_throttle') return 'Aggressive Throttle';
    if (evt === 'speeding') return 'Speeding';
  }

  if (activeAlert) {
    const lower = activeAlert.toLowerCase();
    if (lower.includes('coolant') || lower.includes('temperature')) return 'Coolant Warning';
    if (lower.includes('brake')) return 'Brake Stress';
    if (lower.includes('rpm')) return 'High RPM';
    if (lower.includes('speed')) return 'Speeding';
    if (lower.includes('throttle') || lower.includes('acceleration')) return 'Aggressive Throttle';
  }

  if (rpm > 2500) return 'High RPM';

  const score = vehicle.healthScore;
  if (score >= 95) return 'Healthy';
  if (score >= 80) return 'Normal';
  if (score >= 65) return 'Minor Stress';
  if (score >= 45) return 'High Stress';
  return 'Critical';
}

export const VehicleHealthBar = memo(function VehicleHealthBar({ vehicle, height = 6 }) {
  const score = vehicle.healthScore ?? 0;
  const smoothScore = useSmoothValue(score);

  const color = getHealthColor(smoothScore);
  const label = getHealthLabel(vehicle);

  return (
    <div style={{ width: '100%' }}>
      <div
        style={{
          width: '100%',
          height,
          borderRadius: 3,
          background: 'var(--color-border-light)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${Math.max(0, Math.min(100, smoothScore))}%`,
            height: '100%',
            borderRadius: 3,
            background: color,
            transition: 'background-color 0.4s ease, width 0.4s ease',
          }}
        />
      </div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 4,
          fontSize: 11,
        }}
      >
        <span style={{ color: 'var(--color-text-secondary)', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>
          {Math.round(smoothScore)}%
        </span>
        <span style={{ color: 'var(--color-text-muted)', transition: 'color 0.3s ease' }}>{label}</span>
      </div>
    </div>
  );
});
