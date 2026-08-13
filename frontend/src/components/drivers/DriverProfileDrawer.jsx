import { useEffect, useRef, useState } from 'react';
import {
  X, TrendingUp, TrendingDown, Minus,
  Gauge, Thermometer, Fuel, Activity, AlertTriangle,
  Zap, Cpu, Wind, Route, Trophy, Lightbulb, Clock, ChevronRight,
} from 'lucide-react';
import { useDriver, useDriverPerformance, useDrivers } from '../../hooks/useDrivers';
import { useDriverTrips } from '../../hooks/useDriverTrips';
import { useSmoothValue } from '../../hooks/useSmoothValue';
import { useRelativeTime } from '../../hooks/useRelativeTime';
import { DriverScoreRing } from './DriverScoreRing';
import { DriverRiskBadge } from './DriverRiskBadge';
import { DriverBehaviourTimeline } from './DriverBehaviourTimeline';
import { DriverMetrics } from './DriverMetrics';
import { TripStatusBadge } from '../trips/TripStatusBadge';
import { TripDrawer } from '../trips/TripDrawer';
import { EmptyState } from '../ui/EmptyState';
import { computeDriverBenchmark } from '../../utils/driverBenchmark';
import { generateDriverInsights } from '../../utils/driverInsights';

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

const TABS = ['Overview', 'Live', 'Trips', 'Performance', 'Behaviour', 'Insights'];

function gradeColor(grade) {
  if (!grade) return 'var(--color-text-muted)';
  if (grade === 'A') return 'var(--color-green)';
  if (grade === 'B') return 'var(--color-accent)';
  if (grade === 'C' || grade === 'D') return 'var(--color-amber)';
  return 'var(--color-red)';
}

export function DriverProfileDrawer({ driverId, onClose }) {
  const driver = useDriver(driverId);
  const [activeTab, setActiveTab] = useState('Overview');

  return (
    <DrawerFrame onClose={onClose}>
      {driver ? (
        <DrawerContent
          driver={driver}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          onClose={onClose}
        />
      ) : (
        <DrawerEmpty onClose={onClose} />
      )}
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
          width: 500,
          maxWidth: '92vw',
          height: '100vh',
          background: 'var(--color-surface)',
          borderLeft: '1px solid var(--color-border)',
          boxShadow: 'var(--color-shadow-lg)',
          zIndex: 301,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxSizing: 'border-box',
          animation: 'slideInRight 0.2s ease-out',
        }}
      >
        {children}
      </div>
    </>
  );
}

function DrawerContent({ driver, activeTab, onTabChange, onClose }) {
  const [selectedTrip, setSelectedTrip] = useState(null);
  const performance = useDriverPerformance(driver.id);
  const { trips, loading } = useDriverTrips(driver.id);
  const allDrivers = useDrivers();
  const scrollRef = useRef(null);
  const statusStyle = STATUS_MAP[driver.status] || STATUS_MAP.off_duty;

  const historical = driver.historical || {};
  const benchmark = computeDriverBenchmark(driver, allDrivers);
  const insights = generateDriverInsights({ driver, allDrivers });

  const trend = historical.trend ? TREND_LABELS[historical.trend] : null;
  const TrendIcon = trend ? trend.icon : null;

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [activeTab]);

  return (
    <>
      <Header driver={driver} onClose={onClose} statusStyle={statusStyle} />

      <SummaryBlock driver={driver} trend={trend} TrendIcon={TrendIcon} />

      <NavSurface active={activeTab} onChange={onTabChange} />

      <div
        ref={scrollRef}
        style={{
          flex: 1,
          minHeight: 0,
          overflowY: 'auto',
          padding: '12px 20px 20px',
          boxSizing: 'border-box',
        }}
      >
        {activeTab === 'Overview' && <OverviewTab driver={driver} benchmark={benchmark} />}
        {activeTab === 'Live' && <LiveTab driver={driver} />}
        {activeTab === 'Trips' && (
          <TripsTab trips={trips} loading={loading} onTripClick={setSelectedTrip} />
        )}
        {activeTab === 'Performance' && (
          <PerformanceTab driver={driver} performance={performance} />
        )}
        {activeTab === 'Behaviour' && <BehaviourTab driver={driver} />}
        {activeTab === 'Insights' && (
          <InsightsTab insights={insights} benchmark={benchmark} />
        )}
      </div>

      <Footer onClose={onClose} />

      {selectedTrip && (
        <TripDrawer
          key={selectedTrip.id}
          trip={selectedTrip}
          onClose={() => setSelectedTrip(null)}
        />
      )}
    </>
  );
}

function SummaryBlock({ driver, trend, TrendIcon }) {
  const relativeTime = useRelativeTime(driver.lastActive);
  return (
    <div style={{ flexShrink: 0, padding: '16px 20px 0', boxSizing: 'border-box' }}>
      <DualScoreBlocks
        driver={driver}
        relativeTime={relativeTime}
        trend={trend}
        TrendIcon={TrendIcon}
      />
    </div>
  );
}

function DrawerEmpty({ onClose }) {
  return (
    <>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid var(--color-border)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            color: 'var(--color-text-muted)',
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          <Activity size={16} style={{ color: 'var(--color-accent)' }} />
          Driver Details
        </div>
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
      <div
        style={{
          flex: 1,
          minHeight: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 20,
          boxSizing: 'border-box',
        }}
      >
        <EmptyState
          title="Driver unavailable"
          description="The selected driver could not be found. Live data may still be reconnecting — try again in a moment."
          icon={<Activity size={20} />}
        />
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
        flexShrink: 0,
        boxSizing: 'border-box',
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

function DualScoreBlocks({ driver, relativeTime, trend, TrendIcon }) {
  const historical = driver.historical || {};
  const hasLive = driver.status === 'active' && driver.live?.score != null;

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 10,
      }}
    >
      <ScoreBlock
        label="Live Score"
        score={driver.live?.score ?? null}
        subtitle={hasLive ? `Live now · ${relativeTime}` : 'No live telemetry — driver not active'}
        riskLevel={driver.live?.riskLevel || 'unknown'}
        accent={hasLive ? 'var(--color-accent)' : 'var(--color-text-muted)'}
      />
      <ScoreBlock
        label="Historical Safety"
        score={historical.safetyScore}
        subtitle={
          historical.grade
            ? `Grade ${historical.grade} over ${historical.tripsCompleted ?? 0} trips`
            : 'No completed-trip score recorded yet'
        }
        riskLevel={historical.riskLevel || 'unknown'}
        grade={historical.grade}
        accent={
          historical.safetyScore == null
            ? 'var(--color-text-muted)'
            : historical.safetyScore >= 90 ? 'var(--color-green)' :
              historical.safetyScore >= 70 ? 'var(--color-amber)' : 'var(--color-red)'
        }
        trend={trend}
        TrendIcon={TrendIcon}
        scoreDelta={historical.scoreDelta ?? null}
      />
    </div>
  );
}

function ScoreBlock({ label, score, subtitle, riskLevel, grade, accent, trend, TrendIcon, scoreDelta }) {
  return (
    <div
      style={{
        padding: '12px 14px',
        borderRadius: 12,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 6,
      }}
    >
      <div
        style={{
          fontSize: 10,
          fontWeight: 700,
          color: accent,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
        }}
      >
        {label}
      </div>
      <DriverScoreRing score={score} size={72} />
      <DriverRiskBadge level={riskLevel} size="sm" />
      {grade && (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            minWidth: 26,
            height: 22,
            padding: '0 8px',
            borderRadius: 6,
            background: `${gradeColor(grade)}1a`,
            color: gradeColor(grade),
            fontSize: 13,
            fontWeight: 700,
            lineHeight: 1,
          }}
        >
          {grade}
        </span>
      )}
      {trend && TrendIcon ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 11,
            color: trend.color,
            fontWeight: 500,
          }}
        >
          <TrendIcon size={12} strokeWidth={2} />
          {trend.label}
          {scoreDelta != null && Math.abs(scoreDelta) > 0 && (
            <span>{`${scoreDelta > 0 ? '+' : ''}${scoreDelta}`}</span>
          )}
        </div>
      ) : (
        score != null && (
          <span
            style={{
              fontSize: 10,
              color: 'var(--color-text-muted)',
            }}
          >
            Not enough data for a trend
          </span>
        )
      )}
      <div
        style={{
          fontSize: 10,
          color: 'var(--color-text-muted)',
          textAlign: 'center',
          lineHeight: 1.4,
        }}
      >
        {subtitle}
      </div>
    </div>
  );
}

function NavSurface({ active, onChange }) {
  return (
    <div
      style={{
        flexShrink: 0,
        padding: '10px 20px 0',
        boxSizing: 'border-box',
      }}
    >
      <div
        role="tablist"
        aria-label="Driver sections"
        style={{
          display: 'flex',
          gap: 2,
          padding: 4,
          borderRadius: 10,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
          overflowX: 'auto',
          boxSizing: 'border-box',
        }}
      >
        {TABS.map((tab) => {
          const isActive = active === tab;
          return (
            <button
              key={tab}
              role="tab"
              aria-selected={isActive}
              onClick={() => onChange(tab)}
              style={{
                flex: '0 0 auto',
                padding: '7px 12px',
                borderRadius: 7,
                border: 'none',
                background: isActive ? 'var(--color-accent-subtle)' : 'transparent',
                color: isActive ? 'var(--color-accent)' : 'var(--color-text-muted)',
                fontSize: 11,
                fontWeight: 600,
                cursor: 'pointer',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                whiteSpace: 'nowrap',
                transition: 'all 0.12s ease',
              }}
            >
              {tab}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function OverviewTab({ driver, benchmark }) {
  const historical = driver.historical || {};
  const relativeTime = useRelativeTime(driver.lastActive);
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}
    >
      <div
        style={{
          padding: '14px 16px',
          borderRadius: 10,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Activity size={14} style={{ color: 'var(--color-accent)' }} />
          <span
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
            }}
          >
            {driver.vehicleName || 'No vehicle assigned'}
          </span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
          {driver.vehicleId || '—'}
        </div>
        <div
          style={{
            marginTop: 8,
            fontSize: 11,
            color: 'var(--color-text-muted)',
          }}
        >
          {driver.tripsToday > 0 ? `${driver.tripsToday} trip${driver.tripsToday === 1 ? '' : 's'} today` : 'No trips today'}
          <span style={{ margin: '0 4px', opacity: 0.4 }}>·</span>
          {relativeTime}
        </div>
        {historical.percentile != null && (
          <div
            style={{
              marginTop: 8,
              fontSize: 12,
              color: 'var(--color-text-secondary)',
            }}
          >
            <Trophy size={11} style={{ verticalAlign: 'text-bottom', marginRight: 4, color: 'var(--color-amber)' }} />
            {historical.percentile}th percentile for safety across scored drivers
          </div>
        )}
      </div>

      <FleetBenchmark benchmark={benchmark} compact />
    </div>
  );
}

function LiveTab({ driver }) {
  const telemetry = driver.live?.telemetry || {};
  const smoothSpeed = useSmoothValue(telemetry.speed ?? 0);
  const smoothRpm = useSmoothValue(telemetry.rpm ?? 0);
  const smoothThrottle = useSmoothValue(telemetry.throttle ?? 0);
  const smoothBrake = useSmoothValue(telemetry.brake ?? 0);
  const smoothFuel = useSmoothValue(telemetry.fuelLevel ?? 0);
  const smoothCoolant = useSmoothValue(telemetry.coolantTemp ?? 0);
  const smoothEngineLoad = useSmoothValue(telemetry.engineLoad ?? 0);
  const smoothHealth = useSmoothValue(telemetry.healthScore ?? 0);

  const activeEvents = driver.live?.activeEvents || [];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}
    >
      {activeEvents.length > 0 && (
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
            {activeEvents.map((evt) => (
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
      )}

      <div>
        <SectionTitle>Live Telemetry</SectionTitle>
        {driver.status !== 'active' ? (
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
            No live telemetry — the driver is not currently active. Live
            speed, engine and behaviour data will stream here while they
            drive.
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 6,
            }}
          >
            <LiveTelemetryItem icon={<Gauge size={13} />} label="Speed" value={telemetry.speed != null ? `${Math.round(smoothSpeed)} km/h` : '—'} />
            <LiveTelemetryItem icon={<Activity size={13} />} label="RPM" value={telemetry.rpm != null ? Math.round(smoothRpm).toLocaleString() : '—'} />
            <LiveTelemetryItem icon={<Zap size={13} />} label="Throttle" value={telemetry.throttle != null ? `${Math.round(smoothThrottle)}%` : '—'} />
            <LiveTelemetryItem icon={<Wind size={13} />} label="Brake" value={telemetry.brake != null ? `${Math.round(smoothBrake)}%` : '—'} />
            <LiveTelemetryItem icon={<Fuel size={13} />} label="Fuel" value={telemetry.fuelLevel != null ? `${Math.round(smoothFuel)}%` : '—'} />
            <LiveTelemetryItem icon={<Thermometer size={13} />} label="Coolant" value={telemetry.coolantTemp != null ? `${Math.round(smoothCoolant)}\u00b0C` : '—'} />
            <LiveTelemetryItem icon={<Cpu size={13} />} label="Engine Load" value={telemetry.engineLoad != null ? `${Math.round(smoothEngineLoad)}%` : '—'} />
            <LiveTelemetryItem icon={<Activity size={13} />} label="Vehicle Health" value={telemetry.healthScore != null ? `${Math.round(smoothHealth)}%` : '—'} />
          </div>
        )}
      </div>
    </div>
  );
}

function TripsTab({ trips, loading, onTripClick }) {
  return (
    <div>
      <SectionTitle>Completed Trips</SectionTitle>
      {loading ? (
        <div
          style={{
            fontSize: 12,
            color: 'var(--color-text-muted)',
            padding: '8px 2px',
          }}
        >
          Loading trips...
        </div>
      ) : trips.length === 0 ? (
        <EmptyState
          title="No completed trips"
          description="Completed trips for this driver will appear here."
          icon={<Route size={20} />}
        />
      ) : (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
          }}
        >
          {trips.map((trip) => (
            <div
              key={trip.id}
              onClick={() => onTripClick(trip)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 10px',
                borderRadius: 8,
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border-light)',
                cursor: 'pointer',
                transition: 'border-color 0.12s ease',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-accent)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border-light)'; }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  flex: 1,
                  minWidth: 0,
                }}
              >
                <Clock size={12} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 500,
                      color: 'var(--color-text-primary)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {trip.routeName || trip.routeType || trip.routeId || 'Route'}
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: 'var(--color-text-muted)',
                    }}
                  >
                    {trip.completedAt
                      ? new Date(trip.completedAt).toLocaleString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })
                      : 'Completed'}
                    {trip.distanceFormatted && trip.distanceFormatted !== '—'
                      ? ` · ${trip.distanceFormatted}`
                      : ''}
                  </div>
                </div>
              </div>
              <TripStatusBadge status={trip.status} />
              {trip.safetyScore != null ? (
                <span
                  style={{
                    fontSize: 13,
                    fontWeight: 700,
                    fontVariantNumeric: 'tabular-nums',
                    color:
                      trip.safetyScore >= 90 ? 'var(--color-green)' :
                      trip.safetyScore >= 70 ? 'var(--color-amber)' :
                      'var(--color-red)',
                    minWidth: 30,
                    textAlign: 'right',
                  }}
                >
                  {Math.round(trip.safetyScore)}
                </span>
              ) : (
                <span
                  style={{
                    fontSize: 12,
                    color: 'var(--color-text-muted)',
                    minWidth: 30,
                    textAlign: 'right',
                  }}
                >
                  —
                </span>
              )}
              <ChevronRight size={13} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PerformanceTab({ driver, performance }) {
  const historical = driver.historical || {};
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}
    >
      <div>
        <SectionTitle>Historical Scores</SectionTitle>
        <ScoreSummary scores={historical.scores || {}} />
      </div>

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

      <PerformanceTrend
        performance={performance}
        observations={historical.performanceHistory.length}
      />
    </div>
  );
}

function BehaviourTab({ driver }) {
  return (
    <div>
      <DriverBehaviourTimeline driver={driver} />
      {driver.behaviour.totalRatePer100Km != null && (
        <div
          style={{
            marginTop: 8,
            fontSize: 11,
            color: 'var(--color-text-muted)',
            lineHeight: 1.5,
          }}
        >
          {driver.behaviour.totalEvents} recorded event
          {driver.behaviour.totalEvents === 1 ? '' : 's'} across{' '}
          {driver.historical.totalDistanceKm != null
            ? `${Math.round(driver.historical.totalDistanceKm)} km`
            : 'recorded distance'} —{' '}
          {driver.behaviour.totalRatePer100Km} per 100 km.
        </div>
      )}
    </div>
  );
}

function InsightsTab({ insights, benchmark }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}
    >
      <FleetBenchmark benchmark={benchmark} />
      <DriverInsights insights={insights} />
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

function ScoreSummary({ scores }) {
  const items = [
    { label: 'Safety', value: scores?.safety },
    { label: 'Efficiency', value: scores?.efficiency },
    { label: 'Aggression', value: scores?.aggression },
  ];
  const present = items.filter((i) => i.value != null);

  return (
    <div
      style={{
        padding: '12px 14px',
        borderRadius: 8,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
      }}
    >
      {present.length === 0 ? (
        <EmptyState
          title="No scores available"
          description="Safety, efficiency and aggression scores will appear once this driver has completed trips with recorded statistics."
        />
      ) : (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          {items.map((item) => (
            <div
              key={item.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
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
              {item.value == null ? (
                <span
                  style={{
                    fontSize: 13,
                    color: 'var(--color-text-muted)',
                  }}
                >
                  Not available yet
                </span>
              ) : (
                <>
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
                        width: `${Math.max(0, Math.min(100, item.value))}%`,
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
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PerformanceTrend({ performance, observations }) {
  if (!performance || !performance.history || performance.history.length < 2) {
    return (
      <div>
        <SectionTitle>Performance Trend</SectionTitle>
        <EmptyState
          title="Not enough completed trips"
          description="At least two scored trips are needed to plot a performance trend."
        />
      </div>
    );
  }

  const history = performance.history;
  const width = 420;
  const height = 80;
  const padding = { top: 8, bottom: 16, left: 0, right: 0 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const scores = history.map((h) => h.score).filter((s) => s != null);
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
                  {h.date ? new Date(h.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : ''}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      {observations != null && observations < 4 && (
        <div
          style={{
            marginTop: 6,
            fontSize: 11,
            color: 'var(--color-text-muted)',
          }}
        >
          Trend direction is classified once at least 4 completed trips are recorded.
        </div>
      )}
    </div>
  );
}

function FleetBenchmark({ benchmark, compact }) {
  if (!benchmark) {
    return (
      <div>
        <SectionTitle>Fleet Benchmark</SectionTitle>
        <EmptyState
          title="Benchmark not available"
          description="A fleet benchmark needs at least three drivers with recorded safety scores."
          icon={<Trophy size={20} />}
        />
      </div>
    );
  }

  return (
    <div>
      <SectionTitle>Fleet Benchmark</SectionTitle>
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
            alignItems: 'baseline',
            gap: 8,
            marginBottom: 10,
          }}
        >
          <span
            style={{
              fontSize: 24,
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {benchmark.percentile}
            <span style={{ fontSize: 13, color: 'var(--color-text-muted)', fontWeight: 400 }}>
              th percentile
            </span>
          </span>
          <span
            style={{
              fontSize: 12,
              color: 'var(--color-text-muted)',
            }}
          >
            vs {benchmark.fleetSize} scored drivers
          </span>
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
          }}
        >
          <BenchmarkRow
            label="Fleet average safety"
            value={`${benchmark.fleetAvg} / 100`}
            highlight={benchmark.diff}
          />
          <BenchmarkRow
            label="Event rate"
            value={
              benchmark.driverEventRate != null && benchmark.fleetEventRate != null
                ? `${benchmark.driverEventRate.toFixed(1)} vs fleet ${benchmark.fleetEventRate.toFixed(1)} / 100 km`
                : '—'
            }
          />
          {benchmark.fleetFuelEfficiency != null && !compact && (
            <BenchmarkRow
              label="Fleet fuel efficiency"
              value={`${benchmark.fleetFuelEfficiency.toFixed(1)} km/L`}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function BenchmarkRow({ label, value, highlight }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 10,
      }}
    >
      <span
        style={{
          fontSize: 12,
          color: 'var(--color-text-secondary)',
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontSize: 12,
          fontWeight: 600,
          color:
            highlight == null ? 'var(--color-text-primary)' :
            highlight > 0 ? 'var(--color-green)' :
            highlight < 0 ? 'var(--color-red)' :
            'var(--color-text-primary)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {value}
      </span>
    </div>
  );
}

function DriverInsights({ insights }) {
  return (
    <div>
      <SectionTitle>Insights</SectionTitle>
      {insights.length === 0 ? (
        <EmptyState
          title="No insights available"
          description="Insights will appear as this driver accumulates completed trips and behaviour events."
          icon={<Lightbulb size={20} />}
        />
      ) : (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          {insights.map((insight) => (
            <div
              key={insight.id}
              style={{
                padding: '10px 12px',
                borderRadius: 8,
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border-light)',
                display: 'flex',
                flexDirection: 'column',
                gap: 4,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <Lightbulb
                  size={12}
                  style={{
                    color:
                      insight.severity === 'critical' || insight.severity === 'high'
                        ? 'var(--color-amber)'
                        : 'var(--color-accent)',
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: 'var(--color-text-primary)',
                  }}
                >
                  {insight.title}
                </span>
              </div>
              <span
                style={{
                  fontSize: 11,
                  color: 'var(--color-text-secondary)',
                  lineHeight: 1.5,
                }}
              >
                {insight.observation}
              </span>
              <span
                style={{
                  fontSize: 11,
                  color: 'var(--color-text-muted)',
                  fontStyle: 'italic',
                }}
              >
                {insight.action}
              </span>
            </div>
          ))}
        </div>
      )}
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
        flexShrink: 0,
        boxSizing: 'border-box',
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
