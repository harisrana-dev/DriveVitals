import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  X, Gauge, Activity, Thermometer, Fuel, Cpu,
  AlertTriangle, CheckCircle2, ChevronRight,
} from 'lucide-react';
import { useVehicle } from '../../hooks/useFleetData';
import { useSmoothValue } from '../../hooks/useSmoothValue';
import { useLiveData } from '../../context/useLiveData';
import { StatusBadge } from './StatusBadge';
import {
  canonicalHealthCategory,
  normalizeHealthReasons,
  HEALTH_SEVERITY_COLORS,
  HEALTH_SEVERITY_BG,
  HEALTH_SEVERITY_LABEL,
} from '../../utils/health';
import { dueStatus, dueStatusStyle } from '../../utils/maintenance';
import { drawerStackOffset, drawerZIndex, overlayZIndex } from '../../utils/drawerLayout';

const EVENT_LABELS = {
  speeding: 'Speeding',
  harsh_braking: 'Harsh Braking',
  aggressive_throttle: 'Aggressive Throttle',
  high_rpm: 'High RPM',
};

const MAINTENANCE_TYPE_LABELS = {
  oil_change: 'Oil Change',
  brake_inspection: 'Brake Inspection',
  tyre_rotation: 'Tyre Rotation',
  coolant: 'Coolant',
  general_inspection: 'General Inspection',
  brake_fluid: 'Brake Fluid Service',
  brake_pad_replacement: 'Brake Pad Replacement',
  tyre_pressure: 'Tyre Pressure Check',
};

function titleCase(value) {
  if (!value) return 'Service';
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function VehicleDrawer({ vehicleId, onClose, depth = 0, onOpenMaintenance }) {
  const vehicle = useVehicle(vehicleId);
  const { maintenance } = useLiveData();
  const [expandedEvents, setExpandedEvents] = useState(false);

  if (!vehicle) return null;

  return (
    <DrawerFrame onClose={onClose} depth={depth}>
      <DrawerContent
        vehicle={vehicle}
        vehicleId={vehicleId}
        maintenance={maintenance}
        expandedEvents={expandedEvents}
        onToggleEvents={() => setExpandedEvents((p) => !p)}
        onClose={onClose}
        depth={depth}
        onOpenMaintenance={onOpenMaintenance}
      />
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
          width: 440,
          maxWidth: '90vw',
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

function DrawerContent({ vehicle, vehicleId, maintenance, expandedEvents, onToggleEvents, onClose, onOpenMaintenance }) {
  const status = vehicle.displayStatus || 'OFFLINE';

  const reasons = useMemo(() => normalizeHealthReasons(vehicle.reasons), [vehicle.reasons]);
  const healthCat = useMemo(
    () => canonicalHealthCategory(vehicle.healthScore, null),
    [vehicle.healthScore]
  );
  const activeEvents = vehicle.activeEventTypes || [];
  const visibleEvents = expandedEvents ? activeEvents : activeEvents.slice(0, 3);
  const hiddenCount = Math.max(0, activeEvents.length - 3);

  const vehicleMaintenance = useMemo(() => {
    if (!Array.isArray(maintenance)) return [];
    return maintenance
      .filter((m) => m.vehicle_id === vehicleId && m.status !== 'completed')
      .map((m) => {
        const remainingKm = m.due_odometer_km != null && vehicle.odometer != null
          ? Math.max(0, Math.round(m.due_odometer_km - vehicle.odometer))
          : null;
        const ds = remainingKm != null ? dueStatus(remainingKm) : 'GOOD';
        return {
          id: m.maintenance_id,
          type: MAINTENANCE_TYPE_LABELS[m.maintenance_type] || titleCase(m.maintenance_type),
          dueStatus: ds,
          style: dueStatusStyle(ds),
          remainingKm,
        };
      })
      .sort((a, b) => {
        const order = { OVERDUE: 0, 'DUE SOON': 1, SCHEDULED: 2, GOOD: 3 };
        return (order[a.dueStatus] ?? 4) - (order[b.dueStatus] ?? 4);
      });
  }, [maintenance, vehicleId, vehicle.odometer]);

  return (
    <>
      <Header vehicle={vehicle} status={status} healthCat={healthCat} onClose={onClose} />
      <DriverSection vehicle={vehicle} />
      <div
        className="dashboard-scroll"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        <HealthSignalsSection reasons={reasons} vehicle={vehicle} />
        <ActiveEventsSection
          events={activeEvents}
          visibleEvents={visibleEvents}
          hiddenCount={hiddenCount}
          expandedEvents={expandedEvents}
          onToggleEvents={onToggleEvents}
        />
        <RecentConditionSection vehicle={vehicle} />
        <MaintenanceSection items={vehicleMaintenance} vehicleId={vehicleId} onOpenMaintenance={onOpenMaintenance} />
      </div>
      <DrawerFooter vehicleId={vehicleId} onOpenMaintenance={onOpenMaintenance} />
    </>
  );
}

const AVATAR_BG = 'var(--color-accent-subtle)';

function Header({ vehicle, status, healthCat, onClose }) {
  const initials = vehicle.name
    ? vehicle.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : '—';
  const healthLabelText = healthCat === 'healthy' ? 'Healthy'
    : healthCat === 'warning' ? 'Warning'
    : healthCat === 'critical' ? 'Critical'
    : 'Unavailable';
  const healthColor = healthCat === 'healthy' ? 'var(--color-green)'
    : healthCat === 'warning' ? 'var(--color-amber)'
    : healthCat === 'critical' ? 'var(--color-red)'
    : 'var(--color-text-muted)';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 20px',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: AVATAR_BG,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-accent)',
            fontSize: 14,
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {initials}
        </div>
        <div style={{ minWidth: 0 }}>
          <div
            style={{
              fontSize: 15,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              lineHeight: 1.3,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {vehicle.name}
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              marginTop: 2,
            }}
          >
            <span
              style={{
                fontSize: 11,
                color: 'var(--color-text-muted)',
                fontFamily: 'monospace',
              }}
            >
              {vehicle.id}
            </span>
            <span style={{ color: 'var(--color-border)', fontSize: 11 }}>·</span>
            <span
              style={{
                fontSize: 10,
                color: 'var(--color-text-muted)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {vehicle.driver || '—'}
            </span>
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <StatusBadge status={status} size="sm" />
        <span
          aria-hidden="true"
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: healthColor,
            flexShrink: 0,
          }}
        />
        <span
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: healthColor,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}
        >
          {healthLabelText}
        </span>
        <button
          onClick={onClose}
          aria-label="Close detail panel"
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

function DriverSection({ vehicle }) {
  const initials = vehicle.driver
    ? vehicle.driver.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : '—';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '12px 20px',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      <div
        style={{
          width: 34,
          height: 34,
          borderRadius: 8,
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
        {initials}
      </div>
      <div>
        <div
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: 'var(--color-text-primary)',
            lineHeight: 1.3,
          }}
        >
          {vehicle.driver || 'No driver assigned'}
        </div>
        {vehicle.driverId && (
          <div
            style={{
              fontSize: 10,
              color: 'var(--color-text-muted)',
              fontFamily: 'monospace',
            }}
          >
            {vehicle.driverId}
          </div>
        )}
      </div>
    </div>
  );
}

function SectionTitle({ children, count }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 8,
      }}
    >
      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          color: 'var(--color-text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
        }}
      >
        {children}
      </div>
      {count != null && (
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: 'var(--color-text-muted)',
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {count}
        </span>
      )}
    </div>
  );
}

const SEVERITY_ICON_SIZE = 12;

function SeverityDot({ severity }) {
  const color = HEALTH_SEVERITY_COLORS[severity] || 'var(--color-amber)';
  return (
    <span
      aria-hidden="true"
      style={{
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: color,
        flexShrink: 0,
      }}
    />
  );
}

function HealthSignalsSection({ reasons }) {

  return (
    <div>
      <SectionTitle count={reasons.length}>Health Signals</SectionTitle>
      {reasons.length === 0 ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8,
            padding: '10px 12px',
            borderRadius: 6,
            background: 'var(--color-green-bg)',
            border: '1px solid var(--color-green)',
            fontSize: 12,
          }}
        >
          <CheckCircle2 size={SEVERITY_ICON_SIZE} style={{ color: 'var(--color-green)', flexShrink: 0, marginTop: 1 }} />
          <div>
            <div style={{ fontWeight: 500, color: 'var(--color-green)' }}>No active health signals</div>
            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 2, lineHeight: 1.4 }}>
              All subsystems are operating normally.
            </div>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {reasons.slice(0, 6).map((reason, i) => {
            const sevColor = HEALTH_SEVERITY_COLORS[reason.severity] || 'var(--color-amber)';
            const sevBg = HEALTH_SEVERITY_BG[reason.severity] || 'var(--color-amber-bg)';
            const sevLabel = HEALTH_SEVERITY_LABEL[reason.severity] || 'Warning';
            const title = reason.title || reason.reason;
            const summary = reason.summary && reason.summary !== reason.reason ? reason.summary : '';

            return (
              <div
                key={`${reason.code || reason.reason}-${i}`}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                  padding: '10px 12px',
                  borderRadius: 6,
                  background: sevBg,
                  border: `1px solid ${sevColor}`,
                  fontSize: 12,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <SeverityDot severity={reason.severity} />
                  <span style={{ fontWeight: 500, color: 'var(--color-text-primary)', flex: 1, minWidth: 0 }}>
                    {title}
                  </span>
                  <span
                    style={{
                      fontSize: 9,
                      fontWeight: 700,
                      color: sevColor,
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {sevLabel}
                  </span>
                </div>
                {summary && (
                  <div
                    style={{
                      fontSize: 11,
                      color: 'var(--color-text-secondary)',
                      lineHeight: 1.4,
                      paddingLeft: 10,
                    }}
                  >
                    {summary}
                  </div>
                )}
              </div>
            );
          })}
          {reasons.length > 6 && (
            <div
              style={{
                fontSize: 11,
                color: 'var(--color-text-muted)',
                paddingLeft: 4,
                paddingTop: 2,
              }}
            >
              +{reasons.length - 6} more health signal{reasons.length - 6 > 1 ? 's' : ''}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ActiveEventsSection({ events, visibleEvents, hiddenCount, expandedEvents, onToggleEvents }) {
  return (
    <div>
      <SectionTitle count={events.length}>Active Events</SectionTitle>
      {events.length === 0 ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8,
            padding: '10px 12px',
            borderRadius: 6,
            background: 'var(--color-green-bg)',
            border: '1px solid var(--color-green)',
            fontSize: 12,
          }}
        >
          <CheckCircle2 size={14} style={{ color: 'var(--color-green)', flexShrink: 0, marginTop: 1 }} />
          <div>
            <div style={{ fontWeight: 500, color: 'var(--color-green)' }}>No active events</div>
            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 2, lineHeight: 1.4 }}>
              Vehicle is operating normally.
            </div>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {visibleEvents.map((evt) => (
            <div
              key={evt}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 12px',
                borderRadius: 6,
                background: 'var(--color-red-bg)',
                border: '1px solid var(--color-red)',
                fontSize: 12,
              }}
            >
              <AlertTriangle size={12} style={{ color: 'var(--color-red)', flexShrink: 0 }} />
              <span
                style={{
                  fontWeight: 500,
                  color: 'var(--color-red)',
                  flex: 1,
                }}
              >
                {EVENT_LABELS[evt] || evt}
              </span>
            </div>
          ))}
          {hiddenCount > 0 && (
            <button
              onClick={onToggleEvents}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '6px 10px',
                borderRadius: 6,
                border: '1px dashed var(--color-border)',
                background: 'transparent',
                color: 'var(--color-text-muted)',
                fontSize: 11,
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-accent)';
                e.currentTarget.style.color = 'var(--color-accent)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border)';
                e.currentTarget.style.color = 'var(--color-text-muted)';
              }}
            >
              <ChevronRight
                size={12}
                style={{
                  transform: expandedEvents ? 'rotate(90deg)' : 'none',
                  transition: 'transform 0.15s ease',
                }}
              />
              {expandedEvents ? 'Show less' : `+${hiddenCount} more`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function getMetricState(type, value) {
  if (value == null || typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }
  switch (type) {
    case 'rpm':
      if (value >= 6200) return { label: 'Critical', severity: 'critical' };
      if (value >= 5000) return { label: 'Elevated', severity: 'warning' };
      return null;
    case 'coolant':
      if (value >= 105) return { label: 'Critical', severity: 'critical' };
      if (value >= 95) return { label: 'Elevated', severity: 'warning' };
      return null;
    case 'load':
      if (value >= 85) return { label: 'Critical', severity: 'critical' };
      if (value >= 70) return { label: 'High', severity: 'warning' };
      return null;
    case 'fuel':
      if (value <= 15) return { label: 'Low', severity: 'critical' };
      if (value <= 40) return { label: 'Moderate', severity: 'warning' };
      return null;
    default:
      return null;
  }
}

function TelemetryMetric({ icon, label, value, stateLabel, stateColor }) {
  const hasState = stateLabel && stateColor;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        padding: '8px 10px',
        borderRadius: 6,
        background: 'var(--color-bg)',
        border: hasState ? `1px solid ${stateColor}` : '1px solid var(--color-border-light)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          color: 'var(--color-text-muted)',
          fontSize: 10,
        }}
      >
        {icon}
        <span>{label}</span>
      </div>
      <div
        style={{
          fontSize: 15,
          fontWeight: 700,
          color: hasState ? stateColor : 'var(--color-text-primary)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {value}
      </div>
      {hasState && (
        <div style={{ fontSize: 9, color: stateColor, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          {stateLabel}
        </div>
      )}
    </div>
  );
}

function RecentConditionSection({ vehicle }) {
  const smoothSpeed = useSmoothValue(vehicle.speed);
  const smoothRpm = useSmoothValue(vehicle.rpm);
  const smoothCoolant = useSmoothValue(vehicle.coolantTemp);
  const smoothEngineLoad = useSmoothValue(vehicle.engineLoad ?? 0);
  const smoothFuel = useSmoothValue(vehicle.fuelLevel);

  const coolState = getMetricState('coolant', vehicle.coolantTemp);
  const loadState = getMetricState('load', vehicle.engineLoad);
  const rpmState = getMetricState('rpm', vehicle.rpm);
  const fuelState = getMetricState('fuel', vehicle.fuelLevel);

  const metricStateColor = (state) =>
    state?.severity === 'critical' ? 'var(--color-red)'
      : state?.severity === 'warning' ? 'var(--color-amber)'
    : null;

  const metricStateLabel = (state) => state?.label || '';

  return (
    <div>
      <SectionTitle>Recent Condition</SectionTitle>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 8,
        }}
      >
        <TelemetryMetric
          icon={<Gauge size={12} />}
          label="Speed"
          value={vehicle.speed != null && vehicle.speed > 0 ? `${Math.round(smoothSpeed)} km/h` : '—'}
        />
        <TelemetryMetric
          icon={<Activity size={12} />}
          label="RPM"
          value={vehicle.rpm != null && vehicle.rpm > 0 ? Math.round(smoothRpm).toLocaleString() : '—'}
          stateLabel={metricStateLabel(rpmState)}
          stateColor={metricStateColor(rpmState)}
        />
        <TelemetryMetric
          icon={<Thermometer size={12} />}
          label="Coolant"
          value={vehicle.coolantTemp > 0 ? `${Math.round(smoothCoolant)}°C` : '—'}
          stateLabel={metricStateLabel(coolState)}
          stateColor={metricStateColor(coolState)}
        />
        <TelemetryMetric
          icon={<Cpu size={12} />}
          label="Engine Load"
          value={vehicle.engineLoad != null ? `${Math.round(smoothEngineLoad)}%` : '—'}
          stateLabel={metricStateLabel(loadState)}
          stateColor={metricStateColor(loadState)}
        />
        <TelemetryMetric
          icon={<Fuel size={12} />}
              label="Fuel Level"
          value={`${Math.round(smoothFuel)}%`}
          stateLabel={metricStateLabel(fuelState)}
          stateColor={metricStateColor(fuelState)}
        />
      </div>
    </div>
  );
}

function MaintenanceSection({ items, vehicleId, onOpenMaintenance }) {
  const handleOpen = onOpenMaintenance
    ? () => onOpenMaintenance(vehicleId)
    : undefined;
  return (
    <div>
      <SectionTitle count={items.length}>Maintenance</SectionTitle>
      {items.length === 0 ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8,
            padding: '10px 12px',
            borderRadius: 6,
            background: 'var(--color-green-bg)',
            border: '1px solid var(--color-green)',
            fontSize: 12,
          }}
        >
          <CheckCircle2 size={14} style={{ color: 'var(--color-green)', flexShrink: 0, marginTop: 1 }} />
          <div>
            <div style={{ fontWeight: 500, color: 'var(--color-green)' }}>All scheduled services healthy</div>
            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 2, lineHeight: 1.4 }}>
              No services due.
            </div>
          </div>
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {items.slice(0, 4).map((item) => (
              <div
                key={item.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 8,
                  padding: '8px 10px',
                  borderRadius: 6,
                  background: 'var(--color-bg)',
                  border: '1px solid var(--color-border-light)',
                }}
              >
                <span
                  style={{
                    fontSize: 12,
                    color: 'var(--color-text-primary)',
                    fontWeight: 500,
                    minWidth: 0,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {item.type}
                </span>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: 4,
                    background: item.style.bg,
                    color: item.style.color,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {item.dueStatus}
                </span>
              </div>
            ))}
            {items.length > 4 && (
              <div
                style={{
                  fontSize: 11,
                  color: 'var(--color-text-muted)',
                  paddingLeft: 4,
                  paddingTop: 2,
                }}
              >
                +{items.length - 4} more scheduled services
              </div>
            )}
          </div>
          <div style={{ marginTop: 8 }}>
            {onOpenMaintenance ? (
              <button
                onClick={handleOpen}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  fontSize: 12,
                  fontWeight: 500,
                  color: 'var(--color-accent)',
                  textDecoration: 'none',
                  transition: 'color 0.15s ease',
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.textDecoration = 'underline'; }}
                onMouseLeave={(e) => { e.currentTarget.style.textDecoration = 'none'; }}
              >
                Open Maintenance
                <span aria-hidden="true" style={{ fontSize: 14 }}>{'\u2192'}</span>
              </button>
            ) : (
              <Link
                to={`/maintenance?vehicle=${encodeURIComponent(vehicleId || '')}`}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  fontSize: 12,
                  fontWeight: 500,
                  color: 'var(--color-accent)',
                  textDecoration: 'none',
                  transition: 'color 0.15s ease',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.textDecoration = 'underline'; }}
                onMouseLeave={(e) => { e.currentTarget.style.textDecoration = 'none'; }}
              >
                Open Maintenance
                <span aria-hidden="true" style={{ fontSize: 14 }}>{'\u2192'}</span>
              </Link>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function DrawerFooter({ vehicleId, onOpenMaintenance }) {
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
        style={{
          flex: 1,
          padding: '8px 12px',
          borderRadius: 8,
          background: 'var(--color-accent)',
          color: '#fff',
          fontSize: 13,
          fontWeight: 500,
          border: 'none',
          cursor: 'pointer',
          transition: 'opacity 0.15s ease',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.85'; }}
        onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
      >
        Acknowledge
      </button>
      {onOpenMaintenance ? (
        <button
          onClick={() => onOpenMaintenance(vehicleId)}
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'transparent',
            color: 'var(--color-text-secondary)',
            fontSize: 13,
            fontWeight: 500,
            textDecoration: 'none',
            transition: 'all 0.15s ease',
            cursor: 'pointer',
            fontFamily: 'inherit',
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
          Open Maintenance
        </button>
      ) : (
        <Link
          to={`/maintenance?vehicle=${encodeURIComponent(vehicleId || '')}`}
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'transparent',
            color: 'var(--color-text-secondary)',
            fontSize: 13,
            fontWeight: 500,
            textDecoration: 'none',
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
          Open Maintenance
        </Link>
      )}
    </div>
  );
}
