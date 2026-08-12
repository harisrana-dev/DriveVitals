import { memo, useState } from 'react';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import { HealthStatusBadge } from './HealthStatusBadge';
import { HealthBar } from './HealthBar';
import { componentLabel, topHealthReason, healthReasonLabel, HEALTH_SEVERITY_COLORS } from '../../utils/health';

const COMPONENT_KEYS = ['engine', 'cooling', 'braking', 'transmission', 'fuel'];

export const VehicleHealthCard = memo(function VehicleHealthCard({ vehicle, onClick, index }) {
  const [hovered, setHovered] = useState(false);
  const hasIssues = vehicle.activeEvents.length > 0;
  const hasScore = vehicle.overallHealth != null;
  const topReason = topHealthReason(vehicle.healthReasons);
  const ringColor = hasScore
    ? vehicle.healthCategory === 'healthy' ? 'var(--color-green)'
      : vehicle.healthCategory === 'warning' ? 'var(--color-amber)'
      : 'var(--color-red)'
    : 'var(--color-border)';

  return (
    <div
      className={`fade-in stagger-${(index % 6) + 1}`}
      onClick={() => onClick(vehicle.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: 'var(--color-surface)',
        border: `1px solid ${hovered ? 'var(--color-accent)' : 'var(--color-border)'}`,
        borderRadius: 12,
        padding: 20,
        cursor: 'pointer',
        transition: 'transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease',
        transform: hovered ? 'translateY(-2px)' : 'none',
        boxShadow: hovered ? 'var(--color-shadow-md)' : 'none',
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <div style={{ minWidth: 0, flex: 1 }}>
          <div
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {vehicle.name}
          </div>
          <div
            style={{
              fontSize: 11,
              color: 'var(--color-text-muted)',
              fontFamily: 'monospace',
            }}
          >
            {vehicle.id}
          </div>
        </div>
        <HealthStatusBadge category={vehicle.healthCategory} size="sm" />
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 6,
          padding: '10px 0',
        }}
      >
        <div style={{ position: 'relative', width: 72, height: 72 }}>
          <svg width={72} height={72} viewBox="0 0 72 72">
            <circle cx={36} cy={36} r={30} fill="none" stroke="var(--color-border-light)" strokeWidth={5} />
            <circle
              cx={36}
              cy={36}
              r={30}
              fill="none"
              stroke={ringColor}
              strokeWidth={5}
              strokeDasharray={hasScore ? `${(vehicle.overallHealth / 100) * 188.5} 188.5` : `0 188.5`}
              strokeDashoffset={0}
              strokeLinecap="round"
              transform="rotate(-90 36 36)"
              style={{ transition: 'stroke-dasharray 0.4s ease' }}
            />
            <text x={36} y={36} textAnchor="middle" dy="4" fontSize="16" fontWeight="700" fill="var(--color-text-primary)">
              {hasScore ? Math.round(vehicle.overallHealth) : '\u2014'}
            </text>
          </svg>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '6px 12px',
        }}
      >
        {COMPONENT_KEYS.map((key) => (
          <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>
              {componentLabel(key)}
            </span>
            <HealthBar score={vehicle.components[key]} status={vehicle.componentsStatus[key]} height={4} />
          </div>
        ))}
      </div>

      <div
        style={{
          paddingTop: 4,
          borderTop: '1px solid var(--color-border-light)',
          fontSize: 11,
          display: 'flex',
          alignItems: 'center',
          gap: 5,
          color: topReason ? (HEALTH_SEVERITY_COLORS[topReason.severity] || 'var(--color-amber)') : hasIssues ? 'var(--color-red)' : 'var(--color-green)',
          fontWeight: 500,
          minWidth: 0,
        }}
      >
        {topReason ? (
          <>
            <AlertTriangle size={11} style={{ flexShrink: 0 }} />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {topReason.title || healthReasonLabel(topReason.reason)}
            </span>
          </>
        ) : hasIssues ? (
          <>
            <AlertTriangle size={11} />
            {vehicle.activeEvents.length} active issue{vehicle.activeEvents.length > 1 ? 's' : ''}
          </>
        ) : (
          <>
            <CheckCircle2 size={11} />
            No active issues
          </>
        )}
      </div>
    </div>
  );
});
