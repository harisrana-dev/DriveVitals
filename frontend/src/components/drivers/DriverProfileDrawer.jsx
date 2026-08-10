import {
  X, TrendingUp, TrendingDown, Minus,
  Gauge, Thermometer, Fuel, Activity, AlertTriangle,
  Zap, Cpu, Wind,
} from 'lucide-react';
import { useDriver, useDriverPerformance } from '../../hooks/useDrivers';
import { useSmoothValue } from '../../hooks/useSmoothValue';
import { useRelativeTime } from '../../hooks/useRelativeTime';
import { DriverScoreRing } from './DriverScoreRing';
import { DriverRiskBadge } from './DriverRiskBadge';
import { DriverBehaviourTimeline } from './DriverBehaviourTimeline';
import { DriverMetrics } from './DriverMetrics';

const STATUS_MAP = {
  active: { label: 'ACTIVE', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  off_duty: { label: 'OFF DUTY', color: 'var(--color-text-muted)', bg: 'var(--color-bg)' },
  offline: { label: 'OFFLINE', color: 'var(--color-text-muted)', bg: 'var(--color-bg)' },
};

const TREND_LABELS = {
  improving: { label: 'Improving', icon: TrendingUp, color: 'var(--color-green)' },
  stable: { label: 'Stable', icon: Minus, color: 'var(--color-text-muted)' },
  declining: { label: 'Declining', icon: TrendingDown, color: 'var(--color-red)' },
};

export function DriverProfileDrawer({ driverId, onClose }) {
  const driver = useDriver(driverId);
  if (!driver) return null;

  return (
    <DrawerFrame onClose={onClose}>
      <DrawerContent driver={driver} onClose={onClose} />
    </DrawerFrame>
  );
}

function DrawerFrame({ onClose, children }) {
  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.3)',
          zIndex: 300,
          animation: 'fadeIn 0.15s ease-out',
        }}
      />
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          width: 480,
          maxWidth: '90vw',
          height: '100vh',
          background: 'var(--color-surface)',
          borderLeft: '1px solid var(--color-border)',
          boxShadow: 'var(--color-shadow-lg)',
          zIndex: 301,
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideInRight 0.2s ease-out',
        }}
      >
        {children}
      </div>
    </>
  );
}

function DrawerContent({ driver, onClose }) {
  const performance = useDriverPerformance(driver.id);
  const relativeTime = useRelativeTime(driver.lastActive);
  const statusStyle = STATUS_MAP[driver.status] || STATUS_MAP.off_duty;
  const trend = TREND_LABELS[driver.trend] || TREND_LABELS.stable;
  const TrendIcon = trend.icon;

  const smoothSpeed = useSmoothValue(driver.speed ?? 0);
  const smoothRpm = useSmoothValue(driver.rpm ?? 0);
  const smoothThrottle = useSmoothValue(driver.throttle ?? 0);
  const smoothBrake = useSmoothValue(driver.brake ?? 0);
  const smoothFuel = useSmoothValue(driver.fuelLevel ?? 0);
  const smoothCoolant = useSmoothValue(driver.coolantTemp ?? 0);
  const smoothEngineLoad = useSmoothValue(driver.engineLoad ?? 0);
  const smoothHealth = useSmoothValue(driver.healthScore ?? 0);

  const activeEvents = driver.activeEventTypes || [];

  return (
    <>
      <Header driver={driver} onClose={onClose} statusStyle={statusStyle} />

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 20,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
        }}
      >
        <PerformanceOverview
          driver={driver}
          relativeTime={relativeTime}
          trend={trend}
          TrendIcon={TrendIcon}
          smoothHealth={smoothHealth}
        />

        <div>
          <SectionTitle>Live Telemetry</SectionTitle>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 6,
            }}
          >
            <LiveTelemetryItem icon={<Gauge size={13} />} label="Speed" value={`${Math.round(smoothSpeed)} km/h`} />
            <LiveTelemetryItem icon={<Activity size={13} />} label="RPM" value={Math.round(smoothRpm).toLocaleString()} />
            <LiveTelemetryItem icon={<Zap size={13} />} label="Throttle" value={`${Math.round(smoothThrottle)}%`} />
            <LiveTelemetryItem icon={<Wind size={13} />} label="Brake" value={`${Math.round(smoothBrake)}%`} />
            <LiveTelemetryItem icon={<Fuel size={13} />} label="Fuel" value={`${Math.round(smoothFuel)}%`} />
            <LiveTelemetryItem icon={<Thermometer size={13} />} label="Coolant" value={driver.coolantTemp > 0 ? `${Math.round(smoothCoolant)}\u00b0C` : 'N/A'} />
            <LiveTelemetryItem icon={<Cpu size={13} />} label="Engine Load" value={`${Math.round(smoothEngineLoad)}%`} />
            <LiveTelemetryItem icon={<Activity size={13} />} label="Health" value={`${Math.round(smoothHealth)}%`} />
          </div>
        </div>

        {activeEvents.length > 0 && (
          <ActiveEventsSection events={activeEvents} />
        )}

        <BehaviourSummary scoreBreakdown={driver.scoreBreakdown} />

        <div>
          <SectionTitle>Metrics</SectionTitle>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 8,
            }}
          >
            <DriverMetrics driver={driver} />
          </div>
        </div>

        <DriverBehaviourTimeline driver={driver} />

        <PerformanceTrend performance={performance} />

        <BehaviourDistribution distribution={driver.behaviourDistribution} />
      </div>

      <Footer onClose={onClose} />
    </>
  );
}

function Header({ driver, onClose, statusStyle }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 20px',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: 'var(--color-accent-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-accent)',
            fontSize: 14,
            fontWeight: 600,
            flexShrink: 0,
          }}
        >
          {driver.initials}
        </div>
        <div>
          <div
            style={{
              fontSize: 16,
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
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
        <button
          onClick={onClose}
          aria-label="Close"
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-text-muted)',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-surface-hover)';
            e.currentTarget.style.color = 'var(--color-text-primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'var(--color-text-muted)';
          }}
        >
          <X size={18} />
        </button>
      </div>
    </div>
  );
}

function PerformanceOverview({ driver, relativeTime, trend, TrendIcon, smoothHealth }) {
  return (
    <div
      style={{
        display: 'flex',
        gap: 16,
        padding: '16px 18px',
        borderRadius: 12,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
      }}
    >
      <DriverScoreRing score={smoothHealth} size={88} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8, justifyContent: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <DriverRiskBadge level={driver.riskLevel} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: trend.color, fontWeight: 500 }}>
            <TrendIcon size={13} strokeWidth={2} />
            {trend.label}
          </div>
        </div>
        <div
          style={{
            fontSize: 13,
            color: 'var(--color-text-primary)',
            fontWeight: 500,
          }}
        >
          {driver.vehicleName}
        </div>
        <div
          style={{
            fontSize: 11,
            color: 'var(--color-text-muted)',
          }}
        >
          {driver.tripsToday > 0 ? `${driver.tripsToday} trips today` : 'No trips today'}
          <span style={{ margin: '0 4px', opacity: 0.4 }}>·</span>
          {relativeTime}
        </div>
      </div>
    </div>
  );
}

function ActiveEventsSection({ events }) {
  return (
    <div
      style={{
        padding: '12px 14px',
        borderRadius: 8,
        background: 'var(--color-red-bg)',
        border: '1px solid var(--color-red)',
      }}
    >
      <SectionTitle>Active Events</SectionTitle>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {events.map((evt) => (
          <div
            key={evt}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              color: 'var(--color-red)',
              fontWeight: 500,
            }}
          >
            <AlertTriangle size={11} style={{ flexShrink: 0 }} />
            {evt.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
          </div>
        ))}
      </div>
    </div>
  );
}

function LiveTelemetryItem({ icon, label, value }) {
  return (
    <div
      style={{
        padding: '8px 10px',
        borderRadius: 8,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 5,
          color: 'var(--color-text-muted)',
          marginBottom: 3,
        }}
      >
        {icon}
        <span style={{ fontSize: 10 }}>{label}</span>
      </div>
      <div
        style={{
          fontSize: 14,
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

function BehaviourSummary({ scoreBreakdown }) {
  const breakdown = scoreBreakdown || {};
  const items = [
    { label: 'Braking', value: breakdown.braking || 0 },
    { label: 'Acceleration', value: breakdown.acceleration || 0 },
    { label: 'Speed Compliance', value: breakdown.speed || 0 },
    { label: 'Efficiency', value: breakdown.efficiency || 0 },
  ];

  return (
    <div>
      <SectionTitle>Score Breakdown</SectionTitle>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
        }}
      >
        {items.map((item) => (
          <div
            key={item.label}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '6px 0',
            }}
          >
            <span
              style={{
                width: 100,
                fontSize: 12,
                color: 'var(--color-text-secondary)',
                flexShrink: 0,
              }}
            >
              {item.label}
            </span>
            <div
              style={{
                flex: 1,
                height: 6,
                borderRadius: 3,
                background: 'var(--color-border-light)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${item.value}%`,
                  height: '100%',
                  borderRadius: 3,
                  background:
                    item.value >= 90 ? 'var(--color-green)' :
                    item.value >= 70 ? 'var(--color-amber)' :
                    'var(--color-red)',
                  transition: 'width 0.4s ease',
                }}
              />
            </div>
            <span
              style={{
                width: 32,
                fontSize: 13,
                fontWeight: 600,
                fontVariantNumeric: 'tabular-nums',
                color: 'var(--color-text-primary)',
                textAlign: 'right',
              }}
            >
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function PerformanceTrend({ performance }) {
  if (!performance || !performance.history || performance.history.length < 2) return null;

  const history = performance.history;
  const width = 400;
  const height = 80;
  const padding = { top: 8, bottom: 16, left: 0, right: 0 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const scores = history.map((h) => h.score);
  const min = Math.max(0, Math.min(...scores) - 5);
  const max = Math.min(100, Math.max(...scores) + 5);
  const range = max - min || 1;

  const points = history.map((h, i) => {
    const x = padding.left + (i / (history.length - 1)) * chartW;
    const y = padding.top + chartH - ((h.score - min) / range) * chartH;
    return `${x},${y}`;
  });

  const lineColor =
    scores[scores.length - 1] >= 90 ? 'var(--color-green)' :
    scores[scores.length - 1] >= 70 ? 'var(--color-accent)' :
    'var(--color-red)';

  return (
    <div>
      <SectionTitle>Performance Trend</SectionTitle>
      <div
        style={{
          padding: '12px 0 4px',
          borderRadius: 8,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
          overflow: 'hidden',
        }}
      >
        <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={lineColor} stopOpacity="0.15" />
              <stop offset="100%" stopColor={lineColor} stopOpacity="0.01" />
            </linearGradient>
          </defs>
          <polyline
            points={[`${padding.left},${padding.top + chartH}`, ...points, `${padding.left + chartW},${padding.top + chartH}`].join(' ')}
            fill="url(#trendGrad)"
          />
          <polyline
            points={points.join(' ')}
            fill="none"
            stroke={lineColor}
            strokeWidth="1.5"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {history.filter((_, i) => i === 0 || i === history.length - 1 || i === Math.floor(history.length / 2)).map((h, i) => {
            const idx = i === 0 ? 0 : i === 1 ? Math.floor(history.length / 2) : history.length - 1;
            const x = padding.left + (idx / (history.length - 1)) * chartW;
            const y = padding.top + chartH - ((history[idx].score - min) / range) * chartH;
            return (
              <g key={idx}>
                <circle cx={x} cy={y} r="2.5" fill={lineColor} />
                <text x={x} y={height - 2} textAnchor="middle" fontSize="8" fill="var(--color-text-muted)">
                  {history[idx].date.slice(5)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

function BehaviourDistribution({ distribution }) {
  if (!distribution) return null;

  const items = [
    { label: 'Smooth Driving', value: distribution.smoothDriving || 0, color: 'var(--color-green)' },
    { label: 'Harsh Events', value: distribution.harshEvents || 0, color: 'var(--color-red)' },
    { label: 'Overspeed', value: distribution.overspeed || 0, color: 'var(--color-amber)' },
    { label: 'Idle', value: distribution.idle || 0, color: 'var(--color-accent)' },
  ];

  const total = items.reduce((s, i) => s + i.value, 0) || 1;

  return (
    <div>
      <SectionTitle>Behaviour Distribution</SectionTitle>
      <div
        style={{
          padding: '12px 14px',
          borderRadius: 8,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
        }}
      >
        <div
          style={{
            display: 'flex',
            height: 8,
            borderRadius: 4,
            overflow: 'hidden',
            marginBottom: 12,
          }}
        >
          {items.map((item) => (
            <div
              key={item.label}
              style={{
                width: `${(item.value / total) * 100}%`,
                background: item.color,
                transition: 'width 0.4s ease',
              }}
            />
          ))}
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 6,
          }}
        >
          {items.map((item) => (
            <div
              key={item.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 2,
                  background: item.color,
                  flexShrink: 0,
                }}
              />
              <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
                {item.label}
              </span>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  fontVariantNumeric: 'tabular-nums',
                  marginLeft: 'auto',
                }}
              >
                {Math.round((item.value / total) * 100)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <div
      style={{
        fontSize: 11,
        fontWeight: 600,
        color: 'var(--color-text-muted)',
        marginBottom: 8,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
      }}
    >
      {children}
    </div>
  );
}

function Footer({ onClose }) {
  return (
    <div
      style={{
        padding: '12px 20px',
        borderTop: '1px solid var(--color-border)',
        display: 'flex',
        gap: 8,
      }}
    >
      <button
        onClick={onClose}
        style={{
          flex: 1,
          padding: '8px 12px',
          borderRadius: 8,
          border: '1px solid var(--color-border)',
          background: 'transparent',
          color: 'var(--color-text-secondary)',
          fontSize: 13,
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'all 0.15s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'var(--color-surface-hover)';
          e.currentTarget.style.color = 'var(--color-text-primary)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.color = 'var(--color-text-secondary)';
        }}
      >
        Close
      </button>
    </div>
  );
}
