import { memo, useState } from 'react';
import { Gauge, Activity, AlertTriangle, ChevronRight } from 'lucide-react';
import { useRelativeTime } from '../../hooks/useRelativeTime';
import { useSmoothValue } from '../../hooks/useSmoothValue';
import { driverRiskLevel } from '../../services/driverAdapter';
import { DriverScoreRing } from './DriverScoreRing';
import { DriverRiskBadge } from './DriverRiskBadge';

const STATUS_MAP = {
  active: { label: 'ACTIVE', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  off_duty: { label: 'OFF DUTY', color: 'var(--color-text-muted)', bg: 'var(--color-bg)' },
  offline: { label: 'OFFLINE', color: 'var(--color-text-muted)', bg: 'var(--color-bg)' },
};

const LIVE_EVENT_LABELS = {
  speeding: 'Speeding',
  harsh_braking: 'Harsh Braking',
  aggressive_throttle: 'Aggressive Acceleration',
  high_rpm: 'High RPM',
};

function liveEventLabel(type) {
  if (LIVE_EVENT_LABELS[type]) return LIVE_EVENT_LABELS[type];
  return String(type).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function gradeColor(grade) {
  if (!grade) return 'var(--color-text-muted)';
  if (grade === 'A') return 'var(--color-green)';
  if (grade === 'B') return 'var(--color-accent)';
  if (grade === 'C' || grade === 'D') return 'var(--color-amber)';
  return 'var(--color-red)';
}

export const DriverCard = memo(function DriverCard({ driver, onClick, index }) {
  const [hovered, setHovered] = useState(false);
  const relativeTime = useRelativeTime(driver.lastActive);
  const smoothSpeed = useSmoothValue(driver.live.telemetry.speed ?? 0);
  const smoothRpm = useSmoothValue(driver.live.telemetry.rpm ?? 0);

  const statusStyle = STATUS_MAP[driver.status] || STATUS_MAP.off_duty;
  const activeEvents = (driver.live.activeEvents || [])
    .map(liveEventLabel)
    .filter(Boolean);
  const historicalScore = driver.historical?.safetyScore ?? null;
  const grade = driver.historical?.grade || null;
  const riskLevel = driverRiskLevel(driver);

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
            {driver.vehicleName || '—'}
          </div>
          <div
            style={{
              fontSize: 11,
              color: 'var(--color-text-muted)',
              fontFamily: 'monospace',
            }}
          >
            {driver.vehicleId || 'Not assigned'}
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              marginTop: 6,
            }}
          >
            <DriverRiskBadge level={riskLevel} size="sm" />
            {grade && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minWidth: 20,
                  height: 20,
                  padding: '0 6px',
                  borderRadius: 6,
                  background: `${gradeColor(grade)}1a`,
                  color: gradeColor(grade),
                  fontSize: 11,
                  fontWeight: 700,
                  lineHeight: 1,
                }}
              >
                {grade}
              </span>
            )}
          </div>
        </div>
        <DriverScoreRing score={historicalScore} size={68} />
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
          value={driver.live.telemetry.speed != null ? `${Math.round(smoothSpeed)} km/h` : '—'}
        />
        <TelemetryItem
          icon={<Activity size={12} />}
          label="RPM"
          value={driver.live.telemetry.rpm != null ? Math.round(smoothRpm).toLocaleString() : '—'}
        />
      </div>

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 3,
        }}
      >
        {driver.status === 'active' ? (
          activeEvents.length > 0 ? (
            activeEvents.map((label) => (
              <div
                key={label}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 5,
                  fontSize: 11,
                  color: 'var(--color-red)',
                  fontWeight: 500,
                  padding: '2px 0',
                }}
              >
                <AlertTriangle size={10} style={{ flexShrink: 0 }} />
                {label}
              </div>
            ))
          ) : (
            <div
              style={{
                fontSize: 11,
                color: 'var(--color-text-muted)',
                padding: '2px 0',
              }}
            >
              No active behaviour events
            </div>
          )
        ) : (
          <div
            style={{
              fontSize: 11,
              color: 'var(--color-text-muted)',
              padding: '2px 0',
            }}
          >
            No live data
          </div>
        )}
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
          {driver.tripsToday > 0 ? `${driver.tripsToday} trip${driver.tripsToday === 1 ? '' : 's'} today` : 'No trips today'}
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
