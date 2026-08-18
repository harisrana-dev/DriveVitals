import { useState } from 'react';
import {
  X, Gauge, Clock, Route, Fuel,
  Zap, AlertTriangle, Droplets, User, MapPin,
  Sparkles, Radio, Trash2,
} from 'lucide-react';
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { useTrip } from '../../hooks/useTripsData';
import { useTripTelemetry } from '../../hooks/useTripTelemetry';
import { drawerStackOffset, drawerZIndex, overlayZIndex } from '../../utils/drawerLayout';

const SEVERITY_COLORS = {
  severe: 'var(--color-red)',
  moderate: 'var(--color-amber)',
  minor: 'var(--color-text-muted)',
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

function formatTimestamp(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function TripDrawer({ trip, onClose, onDelete, depth = 0 }) {
  if (!trip) return null;

  return (
    <DrawerFrame onClose={onClose} depth={depth}>
      <DrawerContent trip={trip} onClose={onClose} onDelete={onDelete} />
    </DrawerFrame>
  );
}

function DrawerFrame({ onClose, children, depth = 0 }) {
  const right = drawerStackOffset(depth);
  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.3)',
          zIndex: overlayZIndex(depth),
          animation: 'fadeIn 0.15s ease-out',
        }}
      />
      <div
        style={{
          position: 'fixed',
          top: 0,
          right,
          width: 560,
          maxWidth: '94vw',
          height: '100vh',
          background: 'var(--color-surface)',
          borderLeft: '1px solid var(--color-border)',
          boxShadow: 'var(--color-shadow-lg)',
          zIndex: drawerZIndex(depth),
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

function DrawerContent({ trip, onClose, onDelete }) {
  const liveTrip = useTrip(trip.id);
  const current = liveTrip || trip;
  const isActive = current.status === 'in_progress';
  const isAborted = current.status === 'aborted';

  return (
    <>
      <Header trip={current} isActive={isActive} onClose={onClose} />

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 20,
          display: 'flex',
          flexDirection: 'column',
          gap: 22,
        }}
      >
        <TripSummarySection trip={current} isActive={isActive} />
        <TripDriverSection trip={current} />
        <TripBehaviourSection trip={current} />
        <TripTimelineSection events={current.events} />
        <TripTelemetrySection tripId={current.id} isActive={isActive} />
        <TripInsightSection trip={current} isActive={isActive} />
      </div>

      <Footer trip={current} isAborted={isAborted} onDelete={onDelete} onClose={onClose} />
    </>
  );
}

function Header({ trip, isActive, onClose }) {
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
      <div style={{ minWidth: 0 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 2,
          }}
        >
          <span
            style={{
              fontSize: 11,
              color: 'var(--color-text-muted)',
              fontFamily: 'monospace',
            }}
          >
            {trip.id}
          </span>
          {isActive && (
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: 9,
                fontWeight: 700,
                letterSpacing: '0.06em',
                color: 'var(--color-green)',
                background: 'var(--color-green-bg)',
                padding: '2px 7px',
                borderRadius: 20,
                textTransform: 'uppercase',
              }}
            >
              <Radio size={9} />
              Live
            </span>
          )}
        </div>
        <div
          style={{
            fontSize: 16,
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {trip.vehicleName}
        </div>
        <div
          style={{
            fontSize: 11,
            color: 'var(--color-text-muted)',
            marginTop: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 4,
          }}
        >
          <MapPin size={10} />
          {trip.routeName || trip.routeType}
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
          flexShrink: 0,
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
  const hasGrade = !!grade && grade !== '—';
  const color = !hasGrade ? 'var(--color-text-muted)' :
    grade === 'A' ? 'var(--color-green)' :
    grade === 'B' ? 'var(--color-accent)' :
    grade === 'C' ? 'var(--color-amber)' :
    grade === 'D' ? 'var(--color-amber)' :
    'var(--color-red)';

  const bg = !hasGrade ? 'var(--color-surface-hover)' :
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
      {hasGrade && (
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
      )}
      <div>
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-primary)' }}>
          Safety Score
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>
          {score != null ? `${Math.round(score)}%` : '—'}
        </div>
      </div>
    </div>
  );
}

function TripSummarySection({ trip, isActive }) {
  const averageSpeed = trip.averageSpeed > 0 ? `${trip.averageSpeed.toFixed(1)} km/h` : '—';
  const maximumSpeed = trip.maximumSpeed > 0 ? `${trip.maximumSpeed.toFixed(1)} km/h` : '—';

  return (
    <div>
      <SectionTitle>Trip Overview</SectionTitle>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        <GradeBadge grade={trip.grade} score={trip.safetyScore} />

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 8,
          }}
        >
          {isActive && (
            <div style={{ gridColumn: '1 / -1' }}>
              <StatItem
                icon={<Gauge size={14} />}
                label="Current Speed"
                value={trip.currentSpeed != null ? `${Math.round(trip.currentSpeed)} km/h` : '—'}
                valueColor={trip.currentSpeed > 0 ? 'var(--color-green)' : undefined}
              />
            </div>
          )}
          <StatItem icon={<Route size={14} />} label="Distance" value={formatDistance(trip.distance)} />
          <StatItem icon={<Clock size={14} />} label="Duration" value={formatDuration(trip.duration)} />
          <StatItem icon={<Gauge size={14} />} label="Avg Speed" value={averageSpeed} />
          <StatItem icon={<Zap size={14} />} label="Max Speed" value={maximumSpeed} />
          <StatItem icon={<Fuel size={14} />} label="Fuel Used" value={trip.fuelFormatted} />
          <StatItem icon={<Droplets size={14} />} label="Avg Fuel Rate" value={trip.avgFuelRate > 0 ? `${trip.avgFuelRate.toFixed(1)} L/h` : '—'} />
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: 11,
            color: 'var(--color-text-muted)',
            paddingTop: 2,
          }}
        >
          <span>
            Started {formatTimestamp(trip.startedAt)}
          </span>
          <span>
            {isActive
              ? 'In progress'
              : trip.status === 'aborted'
                ? `Aborted ${formatTimestamp(trip.completedAt)}`
                : `Completed ${formatTimestamp(trip.completedAt)}`}
          </span>
        </div>
      </div>
    </div>
  );
}

function TripDriverSection({ trip }) {
  const initials = (trip.driverName || '—')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();

  return (
    <div>
      <SectionTitle>Driver</SectionTitle>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '10px 12px',
          borderRadius: 10,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
        }}
      >
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: '50%',
            background: 'var(--color-accent-subtle)',
            color: 'var(--color-accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 13,
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {initials}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {trip.driverName}
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
            {trip.driverId}
          </div>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            fontSize: 11,
            color: 'var(--color-text-muted)',
          }}
        >
          <User size={11} />
          {trip.vehicleName}
        </div>
      </div>
    </div>
  );
}

function TripBehaviourSection({ trip }) {
  const events = [
    { key: 'speeding', label: 'Speeding', count: trip.speedingCount, duration: trip.speedingDuration },
    { key: 'harsh_braking', label: 'Harsh Braking', count: trip.harshBrakingCount },
    { key: 'aggressive_throttle', label: 'Aggressive Throttle', count: trip.aggressiveThrottleCount, duration: trip.aggressiveThrottleDuration },
    { key: 'high_rpm', label: 'High RPM', count: trip.highRpmCount, duration: trip.highRpmDuration },
  ];

  const totalEvents = events.reduce((s, e) => s + e.count, 0);
  const severityColor = SEVERITY_COLORS[trip.overallSeverity] || 'var(--color-text-muted)';

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
        {totalEvents > 0 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 2,
            }}
          >
            <AlertTriangle size={12} style={{ color: severityColor }} />
            <span style={{ fontSize: 12, color: severityColor, fontWeight: 500 }}>
              {totalEvents} event{totalEvents === 1 ? '' : 's'} detected · {trip.overallSeverity} severity
            </span>
          </div>
        )}

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
              background: evt.count > 0 ? 'var(--color-red-bg)' : 'transparent',
              border: `1px solid ${evt.count > 0 ? 'var(--color-red)' : 'var(--color-border-light)'}`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertTriangle
                size={11}
                style={{
                  color: evt.count > 0 ? 'var(--color-red)' : 'var(--color-text-muted)',
                  flexShrink: 0,
                }}
              />
              <span
                style={{
                  fontSize: 12,
                  color: evt.count > 0 ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
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

  const chronological = (events || [])
    .map((evt) => ({ ...evt, startedAt: evt.started_at || evt.startedAt }))
    .filter((evt) => evt.startedAt)
    .sort((a, b) => new Date(a.startedAt) - new Date(b.startedAt));

  const seen = new Set();
  const deduped = [];
  for (const evt of chronological) {
    const key = `${evt.event_type || evt.label || 'event'}|${evt.startedAt}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(evt);
  }

  if (deduped.length === 0) return null;

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
        {deduped.slice(0, 10).map((evt, i) => (
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
            {i < deduped.length - 1 && (
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
        {deduped.length > 10 && (
          <div
            style={{
              fontSize: 11,
              color: 'var(--color-text-muted)',
              textAlign: 'center',
              padding: '8px 0',
            }}
          >
            +{deduped.length - 10} more events
          </div>
        )}
      </div>
    </div>
  );
}

function ChartTip({ active, payload, label, unit }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: 'var(--chart-tooltip-bg)',
        color: 'var(--chart-tooltip-text)',
        padding: '6px 10px',
        borderRadius: 8,
        fontSize: 11,
        boxShadow: 'var(--color-shadow-md)',
        border: '1px solid var(--color-border)',
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 2 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: 3,
              background: p.stroke || p.color || 'var(--color-accent)',
            }}
          />
          <span style={{ color: 'var(--color-text-secondary)' }}>{p.name}:</span>
          <span style={{ fontWeight: 500 }}>{p.value}{unit}</span>
        </div>
      ))}
    </div>
  );
}

function TripTelemetrySection({ tripId, isActive }) {
  const { rows, summary, loading } = useTripTelemetry(tripId, { active: isActive });

  return (
    <div>
      <SectionTitle>
        Telemetry
        {isActive && (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              marginLeft: 8,
              color: 'var(--color-green)',
              fontSize: 9,
              fontWeight: 700,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            <Radio size={9} />
            live
          </span>
        )}
      </SectionTitle>

      {rows.length === 0 ? (
        <div
          style={{
            padding: '14px 16px',
            borderRadius: 8,
            background: 'var(--color-bg)',
            border: '1px solid var(--color-border-light)',
            fontSize: 12,
            color: 'var(--color-text-muted)',
            lineHeight: 1.6,
          }}
        >
          {loading
            ? 'Loading telemetry samples…'
            : isActive
              ? 'No telemetry samples recorded for this trip yet. Samples will stream in as the trip progresses.'
              : 'No telemetry samples recorded for this trip.'}
        </div>
      ) : (
        <>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: 8,
              marginBottom: 12,
            }}
          >
            <StatItem icon={<Zap size={14} />} label="Peak Speed" value={`${Math.round(summary.maxSpeed)} km/h`} />
            <StatItem icon={<Gauge size={14} />} label="Peak RPM" value={Math.round(summary.maxRpm).toLocaleString()} />
            <StatItem icon={<Droplets size={14} />} label="Avg Load" value={`${Math.round(summary.avgLoad)}%`} />
          </div>

          <TelemetryChart
            title="Speed Profile"
            height={130}
            gradientId="tripSpeedGrad"
            dataKey="speed"
            name="Speed"
            color="var(--color-accent)"
            unit=" km/h"
            rows={rows}
            area
          />
          <TelemetryChart
            title="Throttle & Brake"
            height={120}
            dataKey="throttle"
            name="Throttle"
            color="var(--color-accent)"
            unit="%"
            rows={rows}
            second={{ dataKey: 'brake', name: 'Brake', color: 'var(--color-red)' }}
          />
          <TelemetryChart
            title="Engine RPM"
            height={110}
            dataKey="rpm"
            name="RPM"
            color="var(--color-amber)"
            rows={rows}
          />
          <TelemetryChart
            title="Engine Load"
            height={110}
            dataKey="load"
            name="Load"
            color="var(--color-green)"
            unit="%"
            rows={rows}
            area
          />
          <TelemetryChart
            title="Fuel Rate"
            height={110}
            dataKey="fuelRate"
            name="Fuel Rate"
            color="var(--color-accent)"
            unit=" L/h"
            rows={rows}
            area
          />
          <TelemetryChart
            title="Coolant Temperature"
            height={110}
            dataKey="coolant"
            name="Coolant"
            color="var(--color-red)"
            unit="°C"
            rows={rows}
            area
          />
        </>
      )}
    </div>
  );
}

function TelemetryChart({ title, rows, dataKey, name, color, unit = '', height, gradientId, second, area }) {
  const body = area
    ? (
      <AreaChart data={rows} margin={{ top: 2, right: 2, left: -22, bottom: 0 }}>
        {gradientId && (
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.18} />
              <stop offset="100%" stopColor={color} stopOpacity={0.01} />
            </linearGradient>
          </defs>
        )}
        <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} minTickGap={40} />
        <YAxis tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} width={40} />
        <Tooltip content={<ChartTip unit={unit} />} />
        <Area
          type="monotone"
          dataKey={dataKey}
          name={name}
          stroke={color}
          strokeWidth={1.6}
          fill={gradientId ? `url(#${gradientId})` : color}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    )
    : (
      <LineChart data={rows} margin={{ top: 2, right: 2, left: -22, bottom: 0 }}>
        <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} minTickGap={40} />
        <YAxis tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} width={40} />
        <Tooltip content={<ChartTip unit={unit} />} />
        <Line
          type="monotone"
          dataKey={dataKey}
          name={name}
          stroke={color}
          strokeWidth={1.6}
          dot={false}
          isAnimationActive={false}
        />
        {second && (
          <Line
            type="monotone"
            dataKey={second.dataKey}
            name={second.name}
            stroke={second.color}
            strokeWidth={1.4}
            dot={false}
            isAnimationActive={false}
          />
        )}
      </LineChart>
    );

  return (
    <div
      style={{
        marginBottom: 12,
        padding: '10px 12px 6px',
        borderRadius: 8,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
      }}
    >
      <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {title}
      </div>
      <ResponsiveContainer width="100%" height={height}>
        {body}
      </ResponsiveContainer>
    </div>
  );
}

const GRADE_TEXT = {
  A: 'Excellent driving. No or minimal safety events recorded.',
  B: 'Good driving with occasional minor events.',
  C: 'Average driving. A few behaviour events were detected.',
  D: 'Below average driving with repeated behaviour events.',
  F: 'Poor driving. Frequent or severe safety events recorded.',
};

function buildInsight(trip, isActive) {
  const counts = [
    { label: 'speeding', weight: 3, count: trip.speedingCount },
    { label: 'harsh braking', weight: 2, count: trip.harshBrakingCount },
    { label: 'aggressive throttle', weight: 2, count: trip.aggressiveThrottleCount },
    { label: 'high-RPM driving', weight: 1, count: trip.highRpmCount },
  ];

  let worst = null;
  let worstScore = 0;
  for (const c of counts) {
    const score = c.count * c.weight;
    if (score > worstScore) {
      worstScore = score;
      worst = c;
    }
  }

  const totalEvents = counts.reduce((s, c) => s + c.count, 0);

  if (isActive) {
    const lines = [];
    lines.push(
      `This trip is currently in progress: ${trip.driverName} has covered ` +
      `${formatDistance(trip.distance)} in ${formatDuration(trip.duration)} at an average of ` +
      `${trip.averageSpeed > 0 ? `${trip.averageSpeed.toFixed(1)} km/h` : 'n/a'}.`
    );
    if (totalEvents === 0) {
      lines.push('No behaviour events have been detected so far.');
    } else {
      lines.push(`${totalEvents} behaviour event${totalEvents === 1 ? '' : 's'} so far, with ${worst.label} as the leading risk.`);
    }
    lines.push(
      trip.safetyScore != null
        ? `Current projected safety score: ${Math.round(trip.safetyScore)}%.`
        : 'A safety score will be available once the trip completes.'
    );
    return lines.join(' ');
  }

  const parts = [];
  if (trip.status === 'aborted') {
    parts.push(
      trip.distance != null && trip.duration != null
        ? `${trip.driverName}'s trip was aborted after ${formatDistance(trip.distance)} in ${formatDuration(trip.duration)}.`
        : `${trip.driverName}'s trip was aborted before any telemetry was recorded.`
    );
  } else {
    parts.push(
      `${trip.driverName} completed ${formatDistance(trip.distance)} in ` +
      `${formatDuration(trip.duration)} with an average speed of ` +
      `${trip.averageSpeed > 0 ? `${trip.averageSpeed.toFixed(1)} km/h` : 'n/a'}.`
    );
  }

  if (totalEvents === 0) {
    parts.push('The trip was clean — no behaviour events were detected.');
  } else {
    parts.push(
      `${totalEvents} behaviour event${totalEvents === 1 ? '' : 's'} were detected; ` +
      `${worst.label} was the dominant risk.`
    );
  }

  const grade = trip.grade;
  if (grade && GRADE_TEXT[grade]) {
    parts.push(`Grade ${grade} — ${GRADE_TEXT[grade]}`);
  } else if (trip.safetyScore != null) {
    parts.push(`Final safety score: ${Math.round(trip.safetyScore)}%.`);
  }

  return parts.join(' ');
}

function TripInsightSection({ trip, isActive }) {
  const insight = buildInsight(trip, isActive);

  return (
    <div>
      <SectionTitle>Automated Trip Summary</SectionTitle>
      <div
        style={{
          display: 'flex',
          gap: 10,
          padding: '12px 14px',
          borderRadius: 10,
          background: 'var(--color-accent-subtle)',
          border: '1px solid var(--color-border-light)',
        }}
      >
        <Sparkles
          size={16}
          style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: 2 }}
        />
        <div>
          <p style={{ fontSize: 12, color: 'var(--color-text-primary)', lineHeight: 1.65, margin: 0 }}>
            {insight}
          </p>
          <p style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 8, marginBottom: 0 }}>
            Automated summary generated from trip telemetry and behaviour events.
          </p>
        </div>
      </div>
    </div>
  );
}

function Footer({ trip, isAborted, onDelete, onClose }) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  const handleDelete = async () => {
    if (!onDelete) return;
    setDeleting(true);
    setError(null);
    try {
      await onDelete(trip.id);
      onClose();
    } catch (err) {
      setError(err?.message || 'Failed to delete trip.');
      setDeleting(false);
    }
  };

  return (
    <div
      style={{
        padding: '12px 20px',
        borderTop: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}
    >
      {error && (
        <div
          style={{
            fontSize: 12,
            color: 'var(--color-red)',
            lineHeight: 1.5,
            padding: '8px 12px',
            borderRadius: 8,
            background: 'var(--color-red-bg)',
          }}
        >
          {error}
        </div>
      )}

      {isAborted && onDelete && (
        confirming ? (
          <div
            style={{
              padding: '10px 12px',
              borderRadius: 8,
              background: 'var(--color-red-bg)',
              border: '1px solid var(--color-red)',
            }}
          >
            <div
              style={{
                fontSize: 12,
                color: 'var(--color-text-primary)',
                lineHeight: 1.5,
                marginBottom: 8,
              }}
            >
              Delete this trip permanently? The trip and its associated trip data will be removed.
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => {
                  setConfirming(false);
                  setError(null);
                }}
                disabled={deleting}
                style={{
                  flex: 1,
                  padding: '7px 12px',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                  background: 'transparent',
                  color: 'var(--color-text-secondary)',
                  fontSize: 12,
                  fontWeight: 500,
                  cursor: deleting ? 'default' : 'pointer',
                  opacity: deleting ? 0.6 : 1,
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                style={{
                  flex: 1,
                  padding: '7px 12px',
                  borderRadius: 8,
                  border: '1px solid var(--color-red)',
                  background: 'var(--color-red)',
                  color: '#fff',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: deleting ? 'default' : 'pointer',
                  opacity: deleting ? 0.6 : 1,
                }}
              >
                {deleting ? 'Deleting...' : 'Delete permanently'}
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setConfirming(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px solid var(--color-red)',
              background: 'transparent',
              color: 'var(--color-red)',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--color-red-bg)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <Trash2 size={14} />
            Delete trip
          </button>
        )
      )}

      <div style={{ display: 'flex', gap: 8 }}>
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
    </div>
  );
}
