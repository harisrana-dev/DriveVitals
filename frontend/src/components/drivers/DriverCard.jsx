import { memo, useState } from 'react';
import { Gauge, Activity, Check, AlertTriangle, ChevronRight } from 'lucide-react';
import { useRelativeTime } from '../../hooks/useRelativeTime';
import { useSmoothValue } from '../../hooks/useSmoothValue';
import { DriverScoreRing } from './DriverScoreRing';
import { DriverRiskBadge } from './DriverRiskBadge';

const STATUS_MAP = {
  active: { label: 'ACTIVE', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  off_duty: { label: 'OFF DUTY', color: 'var(--color-text-muted)', bg: 'var(--color-bg)' },
  offline: { label: 'OFFLINE', color: 'var(--color-text-muted)', bg: 'var(--color-bg)' },
};

const BEHAVIOUR_INDICATORS = {
  smoothDriving: { label: 'Smooth Driving', ok: true },
  harshBraking: { label: 'Harsh Braking', ok: false },
  aggressiveAcceleration: { label: 'Aggressive Acceleration', ok: false },
  overspeedEvents: { label: 'Overspeed', ok: false },
  highRpmEvents: { label: 'High RPM', ok: false },
};

export const DriverCard = memo(function DriverCard({ driver, onClick, index }) {
  const [hovered, setHovered] = useState(false);
  const relativeTime = useRelativeTime(driver.lastActive);
  const smoothSpeed = useSmoothValue(driver.speed ?? 0);
  const smoothRpm = useSmoothValue(driver.rpm ?? 0);

  const statusStyle = STATUS_MAP[driver.status] || STATUS_MAP.off_duty;

  const liveBehaviours = driver.activeEventTypes || [];
  const indicators = [
    { ...BEHAVIOUR_INDICATORS.smoothDriving, active: liveBehaviours.length === 0 },
    { ...BEHAVIOUR_INDICATORS.harshBraking, active: driver.harshBraking.active },
    { ...BEHAVIOUR_INDICATORS.aggressiveAcceleration, active: driver.aggressiveAcceleration.active },
    { ...BEHAVIOUR_INDICATORS.overspeedEvents, active: driver.overspeedEvents.active },
    { ...BEHAVIOUR_INDICATORS.highRpmEvents, active: driver.highRpmEvents.active },
  ];

  return (
    <div
      className={`fade-in stagger-${(index % 6) + 1}`}
      onClick={() => onClick(driver)}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'var(--color-accent-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-accent)',
              fontSize: 13,
              fontWeight: 600,
              flexShrink: 0,
            }}
          >
            {driver.initials}
          </div>
          <div>
            <div
              style={{
                fontSize: 14,
                fontWeight: 600,
                color: 'var(--color-text-primary)',
              }}
            >
              {driver.name}
            </div>
            <div
              style={{
                fontSize: 11,
                color: 'var(--color-text-muted)',
                fontFamily: 'monospace',
              }}
            >
              {driver.id}
            </div>
          </div>
        </div>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 5,
            padding: '3px 10px',
            borderRadius: 6,
            background: statusStyle.bg,
            color: statusStyle.color,
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '0.02em',
            lineHeight: 1,
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: statusStyle.color,
              flexShrink: 0,
            }}
          />
          {statusStyle.label}
        </span>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
        }}
      >
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 2 }}>
            Vehicle
          </div>
          <div
            style={{
              fontSize: 13,
              fontWeight: 500,
              color: 'var(--color-text-primary)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {driver.vehicleName}
          </div>
          <div
            style={{
              fontSize: 11,
              color: 'var(--color-text-muted)',
              fontFamily: 'monospace',
            }}
          >
            {driver.vehicleId}
          </div>
        </div>
        <DriverScoreRing score={driver.safetyScore} size={68} />
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 6,
        }}
      >
        <TelemetryItem
          icon={<Gauge size={12} />}
          label="Speed"
          value={`${Math.round(smoothSpeed)} km/h`}
        />
        <TelemetryItem
          icon={<Activity size={12} />}
          label="RPM"
          value={Math.round(smoothRpm).toLocaleString()}
        />
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          flexWrap: 'wrap',
        }}
      >
        <DriverRiskBadge level={driver.riskLevel} size="sm" />
      </div>

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 3,
        }}
      >
        {indicators.map((ind) => (
          <div
            key={ind.label}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              fontSize: 11,
              color: ind.active ? 'var(--color-red)' : 'var(--color-text-muted)',
              fontWeight: ind.active ? 500 : 400,
              padding: '2px 0',
            }}
          >
            {ind.active ? (
              <AlertTriangle size={10} style={{ flexShrink: 0 }} />
            ) : (
              <Check size={10} style={{ flexShrink: 0, color: 'var(--color-green)' }} />
            )}
            {ind.active ? ind.label : `✓ ${ind.label}`}
          </div>
        ))}
      </div>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: 4,
          borderTop: '1px solid var(--color-border-light)',
        }}
      >
        <div
          style={{
            fontSize: 11,
            color: 'var(--color-text-muted)',
          }}
        >
          {driver.tripsToday > 0 ? `${driver.tripsToday} trips today` : 'No trips today'}
          <span style={{ margin: '0 4px', opacity: 0.4 }}>·</span>
          <span>{relativeTime}</span>
        </div>
        <ChevronRight size={13} style={{ color: 'var(--color-text-muted)' }} />
      </div>
    </div>
  );
});

function TelemetryItem({ icon, label, value }) {
  return (
    <div
      style={{
        padding: '6px 8px',
        borderRadius: 6,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          color: 'var(--color-text-muted)',
          marginBottom: 2,
        }}
      >
        {icon}
        <span style={{ fontSize: 10 }}>{label}</span>
      </div>
      <div
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--color-text-primary)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {value}
      </div>
    </div>
  );
}
