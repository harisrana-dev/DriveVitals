import { useMemo } from 'react';
import {
  X, Gauge, Clock, Route, Fuel, Shield, MapPin,
  Zap, Wind, Activity, Thermometer, Cpu, AlertTriangle,
  ChevronUp, ChevronDown, TrendingUp, Droplets,
} from 'lucide-react';
import { useSmoothValue } from '../../hooks/useSmoothValue';

const EVENT_LABELS = {
  speeding: 'Speeding',
  harsh_braking: 'Harsh Braking',
  aggressive_throttle: 'Aggressive Throttle',
  high_rpm: 'High RPM',
};

const SEVERITY_COLORS = {
  severe: 'var(--color-red)',
  moderate: 'var(--color-amber)',
  minor: 'var(--color-text-muted)',
};

const SEVERITY_BG = {
  severe: 'var(--color-red-bg)',
  moderate: 'var(--color-amber-bg)',
  minor: 'transparent',
};

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '—';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

function formatDistance(km) {
  if (km == null || km <= 0) return '—';
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(2)} km`;
}

export function TripDrawer({ trip, onClose }) {
  if (!trip) return null;

  return (
    <DrawerFrame onClose={onClose}>
      <DrawerContent trip={trip} onClose={onClose} />
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
          width: 440,
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

function DrawerContent({ trip, onClose }) {
  const eventTypes = useMemo(() => {
    const types = [];
    if (trip.speedingCount > 0) types.push('speeding');
    if (trip.harshBrakingCount > 0) types.push('harsh_braking');
    if (trip.aggressiveThrottleCount > 0) types.push('aggressive_throttle');
    if (trip.highRpmCount > 0) types.push('high_rpm');
    return types;
  }, [trip]);

  return (
    <>
      <Header trip={trip} onClose={onClose} />

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
        <TripSummarySection trip={trip} />
        <TripBehaviourSection trip={trip} eventTypes={eventTypes} />
        <TripTimelineSection events={trip.events} />
        <TripWearPanel trip={trip} />
        <TripStatisticsSection trip={trip} />
        <TripChartsSection trip={trip} />
      </div>

      <Footer onClose={onClose} />
    </>
  );
}

function Header({ trip, onClose }) {
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
      <div>
        <div
          style={{
            fontSize: 11,
            color: 'var(--color-text-muted)',
            marginBottom: 2,
            fontFamily: 'monospace',
          }}
        >
          {trip.id}
        </div>
        <div
          style={{
            fontSize: 16,
            fontWeight: 600,
            color: 'var(--color-text-primary)',
          }}
        >
          {trip.vehicleName}
        </div>
      </div>
      <button
        onClick={onClose}
        aria-label="Close trip panel"
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

function StatItem({ icon, label, value, valueColor }) {
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
          color: valueColor || 'var(--color-text-primary)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {value}
      </div>
    </div>
  );
}

function GradeBadge({ grade, score }) {
  const color =
    grade === 'A' ? 'var(--color-green)' :
    grade === 'B' ? 'var(--color-accent)' :
    grade === 'C' ? 'var(--color-amber)' :
    grade === 'D' ? 'var(--color-amber)' :
    'var(--color-red)';

  const bg =
    grade === 'A' ? 'var(--color-green-bg)' :
    grade === 'B' ? 'var(--color-accent-subtle)' :
    grade === 'C' ? 'var(--color-amber-bg)' :
    grade === 'D' ? 'var(--color-amber-bg)' :
    'var(--color-red-bg)';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '10px 14px',
        borderRadius: 10,
        background: bg,
        border: `1px solid ${color}`,
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: 18,
          fontWeight: 700,
          flexShrink: 0,
        }}
      >
        {grade}
      </div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-primary)' }}>
          Safety Score
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>
          {Math.round(score)}%
        </div>
      </div>
    </div>
  );
}

function TripSummarySection({ trip }) {
  const smoothSpeed = useSmoothValue(trip.averageSpeed);
  const smoothScore = useSmoothValue(trip.safetyScore);

  return (
    <div>
      <SectionTitle>Trip Summary</SectionTitle>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        <GradeBadge grade={trip.grade} score={smoothScore} />

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 8,
          }}
        >
          <StatItem icon={<Route size={14} />} label="Distance" value={formatDistance(trip.distance)} />
          <StatItem icon={<Clock size={14} />} label="Duration" value={formatDuration(trip.duration)} />
          <StatItem icon={<Gauge size={14} />} label="Avg Speed" value={`${smoothSpeed.toFixed(1)} km/h`} />
          <StatItem icon={<Zap size={14} />} label="Max Speed" value={`${trip.maximumSpeed.toFixed(1)} km/h`} />
          <StatItem icon={<Fuel size={14} />} label="Fuel Used" value={trip.fuelFormatted} />
          <StatItem icon={<Droplets size={14} />} label="Avg Fuel Rate" value={trip.avgFuelRate > 0 ? `${trip.avgFuelRate.toFixed(1)} L/h` : '—'} />
        </div>
      </div>
    </div>
  );
}

function TripBehaviourSection({ trip, eventTypes }) {
  const events = [
    { key: 'speeding', label: 'Speeding', count: trip.speedingCount, duration: trip.speedingDuration },
    { key: 'harsh_braking', label: 'Harsh Braking', count: trip.harshBrakingCount, duration: 0 },
    { key: 'aggressive_throttle', label: 'Aggressive Throttle', count: trip.aggressiveThrottleCount, duration: trip.aggressiveThrottleDuration },
    { key: 'high_rpm', label: 'High RPM', count: trip.highRpmCount, duration: trip.highRpmDuration },
  ];

  const totalEvents = events.reduce((s, e) => s + e.count, 0);

  if (totalEvents === 0) return null;

  return (
    <div>
      <SectionTitle>Driver Behaviour</SectionTitle>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 0.5fr 1fr',
            gap: 4,
            padding: '4px 10px',
            fontSize: 10,
            color: 'var(--color-text-muted)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}
        >
          <span>Event</span>
          <span>Count</span>
          <span>Duration</span>
        </div>
        {events.map((evt) => (
          <div
            key={evt.key}
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 0.5fr 1fr',
              gap: 4,
              alignItems: 'center',
              padding: '6px 10px',
              borderRadius: 6,
              background: evt.count > 0 ? SEVERITY_BG[trip.overallSeverity] : 'transparent',
              border: `1px solid ${evt.count > 0 ? (SEVERITY_COLORS[trip.overallSeverity] || 'var(--color-border-light)') : 'var(--color-border-light)'}`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertTriangle
                size={11}
                style={{
                  color: evt.count > 0 ? SEVERITY_COLORS[trip.overallSeverity] : 'var(--color-text-muted)',
                  flexShrink: 0,
                }}
              />
              <span
                style={{
                  fontSize: 12,
                  color: evt.count > 0 ? SEVERITY_COLORS[trip.overallSeverity] : 'var(--color-text-muted)',
                  fontWeight: evt.count > 0 ? 500 : 400,
                }}
              >
                {evt.label}
              </span>
            </div>
            <span
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: evt.count > 0 ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {evt.count}
            </span>
            <span
              style={{
                fontSize: 12,
                color: evt.count > 0 ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {evt.duration > 0 ? formatDuration(evt.duration) : '—'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TripTimelineSection({ events }) {
  if (!events || events.length === 0) return null;

  return (
    <div>
      <SectionTitle>Trip Timeline</SectionTitle>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 4,
          position: 'relative',
        }}
      >
        {events.slice(0, 10).map((evt, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              gap: 10,
              padding: '6px 0 6px 16px',
              position: 'relative',
            }}
          >
            <div
              style={{
                position: 'absolute',
                left: 4,
                top: 12,
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: SEVERITY_COLORS[evt.severity] || 'var(--color-text-muted)',
                border: '2px solid var(--color-surface)',
              }}
            />
            {i < events.length - 1 && (
              <div
                style={{
                  position: 'absolute',
                  left: 7,
                  top: 22,
                  width: 2,
                  height: 'calc(100% - 10px)',
                  background: 'var(--color-border-light)',
                }}
              />
            )}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 500,
                    color: 'var(--color-text-primary)',
                  }}
                >
                  {evt.label || evt.event_type}
                </span>
                <span
                  style={{
                    fontSize: 10,
                    color: 'var(--color-text-muted)',
                    fontVariantNumeric: 'tabular-nums',
                  }}
                >
                  {evt.duration_seconds ? `${evt.duration_seconds.toFixed(0)}s` : ''}
                </span>
              </div>
              <div
                style={{
                  display: 'flex',
                  gap: 8,
                  marginTop: 2,
                }}
              >
                {evt.severity && (
                  <span
                    style={{
                      fontSize: 10,
                      color: SEVERITY_COLORS[evt.severity],
                      fontWeight: 500,
                      textTransform: 'capitalize',
                    }}
                  >
                    {evt.severity}
                  </span>
                )}
                {evt.distance_km > 0 && (
                  <span style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>
                    {formatDistance(evt.distance_km)}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
        {events.length > 10 && (
          <div
            style={{
              fontSize: 11,
              color: 'var(--color-text-muted)',
              textAlign: 'center',
              padding: '8px 0',
            }}
          >
            +{events.length - 10} more events
          </div>
        )}
      </div>
    </div>
  );
}

function TripWearPanel({ trip }) {
  const totalEvents = trip.speedingCount + trip.harshBrakingCount + trip.aggressiveThrottleCount + trip.highRpmCount;

  if (totalEvents === 0) return null;

  const engineWear = Math.min(100, trip.highRpmCount * 8 + trip.aggressiveThrottleCount * 5);
  const brakeWear = Math.min(100, trip.harshBrakingCount * 12);
  const tyreWear = Math.min(100, trip.speedingCount * 6 + trip.harshBrakingCount * 4);
  const fuelEfficiency = Math.max(0, 100 - (trip.aggressiveThrottleCount * 6 + trip.speedingCount * 3));
  const overallWear = Math.round((engineWear + brakeWear + tyreWear + (100 - fuelEfficiency)) / 4);

  const items = [
    { label: 'Engine Wear', value: engineWear, color: engineWear > 50 ? 'var(--color-red)' : engineWear > 25 ? 'var(--color-amber)' : 'var(--color-green)' },
    { label: 'Brake Wear', value: brakeWear, color: brakeWear > 50 ? 'var(--color-red)' : brakeWear > 25 ? 'var(--color-amber)' : 'var(--color-green)' },
    { label: 'Tyre Wear', value: tyreWear, color: tyreWear > 50 ? 'var(--color-red)' : tyreWear > 25 ? 'var(--color-amber)' : 'var(--color-green)' },
    { label: 'Fuel Efficiency', value: fuelEfficiency, color: fuelEfficiency < 50 ? 'var(--color-red)' : fuelEfficiency < 75 ? 'var(--color-amber)' : 'var(--color-green)' },
  ];

  return (
    <div>
      <SectionTitle>Vehicle Impact</SectionTitle>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '8px 10px',
            borderRadius: 8,
            background: 'var(--color-bg)',
            border: '1px solid var(--color-border-light)',
          }}
        >
          <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)' }}>
            Overall Trip Wear
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <BarIndicator value={overallWear} color={overallWear > 50 ? 'var(--color-red)' : overallWear > 25 ? 'var(--color-amber)' : 'var(--color-green)'} />
            <span style={{ fontSize: 14, fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: 'var(--color-text-primary)' }}>
              {overallWear}%
            </span>
          </div>
        </div>
        {items.map((item) => (
          <div
            key={item.label}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '6px 10px',
              borderRadius: 6,
              background: 'transparent',
              border: '1px solid var(--color-border-light)',
            }}
          >
            <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
              {item.label}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <BarIndicator value={item.value} color={item.color} />
              <span style={{ fontSize: 12, fontWeight: 500, fontVariantNumeric: 'tabular-nums', color: item.color, minWidth: 28, textAlign: 'right' }}>
                {Math.round(item.value)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function BarIndicator({ value, color }) {
  return (
    <div
      style={{
        width: 48,
        height: 4,
        borderRadius: 2,
        background: 'var(--color-border-light)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          width: `${Math.min(100, value)}%`,
          height: '100%',
          background: color,
          borderRadius: 2,
          transition: 'width 0.3s ease',
        }}
      />
    </div>
  );
}

function TripStatisticsSection({ trip }) {
  const stats = [
    { icon: <Activity size={14} />, label: 'Avg RPM', value: trip.highRpmCount > 0 ? `${Math.round(trip.highRpmDuration / Math.max(trip.highRpmCount, 1))}` : '—' },
    { icon: <Zap size={14} />, label: 'Max Speed', value: `${trip.maximumSpeed.toFixed(1)} km/h` },
    { icon: <Gauge size={14} />, label: 'Avg Speed', value: `${trip.averageSpeed.toFixed(1)} km/h` },
    { icon: <Thermometer size={14} />, label: 'Idle Time', value: trip.speedingDuration > 0 ? formatDuration(trip.speedingDuration) : '—' },
    { icon: <Cpu size={14} />, label: 'Engine Runtime', value: formatDuration(trip.duration) },
    { icon: <Fuel size={14} />, label: 'Avg Fuel Rate', value: trip.avgFuelRate > 0 ? `${trip.avgFuelRate.toFixed(1)} L/h` : '—' },
  ];

  return (
    <div>
      <SectionTitle>Telemetry Statistics</SectionTitle>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 8,
        }}
      >
        {stats.map((stat) => (
          <StatItem key={stat.label} icon={stat.icon} label={stat.label} value={stat.value} />
        ))}
      </div>
    </div>
  );
}

function TripChartsSection({ trip }) {
  const segments = [
    { label: 'Speed Profile', value: Math.min(100, (trip.averageSpeed / 120) * 100), color: 'var(--color-accent)', detail: `${trip.averageSpeed.toFixed(0)} km/h avg` },
    { label: 'Fuel Consumption', value: Math.min(100, (trip.fuelConsumed / 10) * 100), color: 'var(--color-amber)', detail: trip.fuelFormatted },
    { label: 'Engine Load', value: Math.min(100, trip.aggressiveThrottleCount * 15 + trip.highRpmCount * 10), color: 'var(--color-red)', detail: `${Math.min(100, trip.aggressiveThrottleCount * 15 + trip.highRpmCount * 10)}%` },
    { label: 'RPM Profile', value: Math.min(100, trip.highRpmCount * 20), color: 'var(--color-green)', detail: `${trip.highRpmCount} events` },
  ];

  return (
    <div>
      <SectionTitle>Trip Charts</SectionTitle>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        {segments.map((seg) => (
          <div
            key={seg.label}
            style={{
              padding: '10px 12px',
              borderRadius: 8,
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border-light)',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 6,
              }}
            >
              <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                {seg.label}
              </span>
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                {seg.detail}
              </span>
            </div>
            <div
              style={{
                width: '100%',
                height: 6,
                borderRadius: 3,
                background: 'var(--color-border-light)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${seg.value}%`,
                  height: '100%',
                  background: seg.color,
                  borderRadius: 3,
                  transition: 'width 0.4s ease',
                }}
              />
            </div>
          </div>
        ))}
      </div>
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
