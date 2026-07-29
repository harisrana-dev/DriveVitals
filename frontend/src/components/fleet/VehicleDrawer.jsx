import { useState } from 'react';
import {
  X, Gauge, Thermometer, Fuel, Activity, AlertTriangle,
  Zap, ChevronUp, ChevronDown, Wind, Cpu, ChevronRight,
} from 'lucide-react';
import { useVehicle } from '../../hooks/useFleetData';
import { useSmoothValue } from '../../hooks/useSmoothValue';
import { useRelativeTime } from '../../hooks/useRelativeTime';
import { StatusBadge } from './StatusBadge';
import { VehicleHealthBar } from './VehicleHealthBar';
import { FuelBar } from './FuelBar';

const EVENT_LABELS = {
  speeding: 'Speeding',
  harsh_braking: 'Harsh Braking',
  aggressive_throttle: 'Aggressive Throttle',
  high_rpm: 'High RPM',
};

function getDisplayStatus(vehicle) {
  if (vehicle.status === 'active' && vehicle.alertCount > 0) return 'ALERT';
  if (vehicle.status === 'active') return 'ACTIVE';
  if (vehicle.status === 'idle') return 'IDLE';
  return vehicle.status.toUpperCase();
}

export function VehicleDrawer({ vehicleId, onClose }) {
  const vehicle = useVehicle(vehicleId);
  const [expandedEvents, setExpandedEvents] = useState(false);

  if (!vehicle) return null;

  return (
    <DrawerFrame onClose={onClose}>
      <DrawerContent vehicle={vehicle} onClose={onClose} expandedEvents={expandedEvents} onToggleEvents={() => setExpandedEvents((p) => !p)} />
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

function DrawerContent({
    vehicle,
    onClose,
    expandedEvents,
    onToggleEvents,
}) {
  const status = getDisplayStatus(vehicle);
  const smoothSpeed = useSmoothValue(vehicle.speed);
  const smoothRpm = useSmoothValue(vehicle.rpm);
  const smoothFuel = useSmoothValue(vehicle.fuelLevel);
  const smoothCoolant = useSmoothValue(vehicle.coolantTemp);
  const smoothThrottle = useSmoothValue(vehicle.throttle ?? 0);
  const smoothBrake = useSmoothValue(vehicle.brake ?? 0);
  const smoothEngineLoad = useSmoothValue(vehicle.engineLoad ?? 0);
  const relativeTime = useRelativeTime(vehicle.lastUpdate);

  const activeEvents = vehicle.activeEventTypes || [];
  const visibleEvents = expandedEvents ? activeEvents : activeEvents.slice(0, 3);
  const hiddenCount = Math.max(0, activeEvents.length - 3);

  return (
    <>
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
            {vehicle.id}
          </div>
          <div
            style={{
              fontSize: 16,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
            }}
          >
            {vehicle.name}
          </div>
        </div>
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
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <StatusBadge status={status} size="lg" />
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
            {relativeTime}
          </span>
        </div>

        <DriverSection vehicle={vehicle} />

        <div>
          <SectionTitle>Operational Health</SectionTitle>
          <VehicleHealthBar vehicle={vehicle} height={8} />
        </div>

        <div>
          <SectionTitle>Telemetry</SectionTitle>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 8,
            }}
          >
            <TelemetryItem icon={<Gauge size={14} />} label="Speed" value={`${Math.round(smoothSpeed)} km/h`} />
            <TelemetryItem icon={<Activity size={14} />} label="RPM" value={Math.round(smoothRpm).toLocaleString()} />
            <TelemetryItem icon={<Zap size={14} />} label="Throttle" value={vehicle.throttle != null ? `${Math.round(smoothThrottle)}%` : '—'} />
            <TelemetryItem icon={<Wind size={14} />} label="Brake" value={vehicle.brake != null ? `${Math.round(smoothBrake * 100)}%` : '—'} />
            <TelemetryItem icon={<Fuel size={14} />} label="Fuel" value={`${Math.round(smoothFuel)}%`} />
            <TelemetryItem icon={<Thermometer size={14} />} label="Coolant" value={vehicle.coolantTemp > 0 ? `${Math.round(smoothCoolant)}°C` : 'N/A'} />
            <TelemetryItem icon={<Cpu size={14} />} label="Engine Load" value={vehicle.engineLoad != null ? `${Math.round(smoothEngineLoad)}%` : '—'} />
          </div>
        </div>

        <div>
          <SectionTitle>Fuel Level</SectionTitle>
          <FuelBar level={vehicle.fuelLevel} />
        </div>

        {activeEvents.length > 0 && (
          <div>
            <SectionTitle>Active Events</SectionTitle>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 4,
              }}
            >
              {visibleEvents.map((evt) => (
                <div
                  key={evt}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '8px 10px',
                    borderRadius: 6,
                    background: 'var(--color-red-bg)',
                    border: '1px solid var(--color-red)',
                  }}
                >
                  <AlertTriangle size={12} style={{ color: 'var(--color-red)', flexShrink: 0 }} />
                  <span style={{ fontSize: 12, color: 'var(--color-red)', fontWeight: 500 }}>
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
                    fontSize: 12,
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
                  <ChevronRight size={12} style={{ transform: expandedEvents ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s ease' }} />
                  {expandedEvents ? 'Show less' : `+${hiddenCount} more`}
                </button>
              )}
            </div>
          </div>
        )}

        <div>
          <SectionTitle>Behaviour Flags</SectionTitle>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 6,
            }}
          >
            <BehaviourFlag active={vehicle.speeding} label="Speeding" />
            <BehaviourFlag active={vehicle.aggressiveThrottle} label="Aggressive Throttle" />
            <BehaviourFlag active={vehicle.harshBraking} label="Harsh Braking" />
            <BehaviourFlag active={vehicle.highRpm} label="High RPM" />
          </div>
        </div>
      </div>

      <DrawerFooter />
    </>
  );
}

function DriverSection({ vehicle }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '12px 14px',
        borderRadius: 10,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
      }}
    >
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
        {vehicle.driver.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
      </div>
      <div>
        <div
          style={{
            fontSize: 14,
            fontWeight: 500,
            color: 'var(--color-text-primary)',
          }}
        >
          {vehicle.driver}
        </div>
        {vehicle.driverId && (
          <div
            style={{
              fontSize: 11,
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

function DrawerFooter() {
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
          transition: 'all 0.15s ease',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-accent-hover)'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-accent)'; }}
      >
        Acknowledge
      </button>
      <button
        style={{
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
        Schedule Service
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

function TelemetryItem({ icon, label, value }) {
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

function BehaviourFlag({ active, label }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '6px 10px',
        borderRadius: 6,
        background: active ? 'var(--color-red-bg)' : 'var(--color-bg)',
        border: `1px solid ${active ? 'var(--color-red)' : 'var(--color-border-light)'}`,
        fontSize: 12,
        color: active ? 'var(--color-red)' : 'var(--color-text-muted)',
        fontWeight: active ? 500 : 400,
        transition: 'all 0.3s ease',
      }}
    >
      {active ? (
        <ChevronUp size={12} />
      ) : (
        <ChevronDown size={12} style={{ opacity: 0.4 }} />
      )}
      {label}
    </div>
  );
}
