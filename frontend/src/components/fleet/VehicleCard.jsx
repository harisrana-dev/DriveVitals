import { memo, useState, useCallback } from 'react';
import { Eye, Gauge, Thermometer, Activity, AlertTriangle, ChevronRight } from 'lucide-react';
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

const STATUS_CACHE = new WeakMap();

function getDisplayStatus(vehicle) {
  if (vehicle.status === 'active' && vehicle.alertCount > 0) return 'ALERT';
  if (vehicle.status === 'active') return 'ACTIVE';
  if (vehicle.status === 'idle') return 'IDLE';
  return vehicle.status.toUpperCase();
}

export const VehicleCard = memo(function VehicleCard({ vehicle, onClick, index }) {
  const [hovered, setHovered] = useState(false);
  const [eventsExpanded, setEventsExpanded] = useState(false);

  const status = getDisplayStatus(vehicle);
  const smoothSpeed = useSmoothValue(vehicle.speed);
  const smoothRpm = useSmoothValue(vehicle.rpm);
  const smoothCoolant = useSmoothValue(vehicle.coolantTemp);
  const relativeTime = useRelativeTime(vehicle.lastUpdate);

  const activeEvents = vehicle.activeEventTypes || [];
  const visibleEvents = eventsExpanded ? activeEvents : activeEvents.slice(0, 2);
  const hiddenCount = activeEvents.length - 2;

  const handleViewDetails = useCallback((e) => {
    e.stopPropagation();
    onClick(vehicle);
  }, [onClick, vehicle]);

  const handleCardClick = useCallback(() => {
    onClick(vehicle);
  }, [onClick, vehicle]);

  const handleToggleEvents = useCallback((e) => {
    e.stopPropagation();
    setEventsExpanded((p) => !p);
  }, []);

  return (
    <div
      className={`fade-in stagger-${(index % 6) + 1}`}
      onClick={handleCardClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: 'var(--color-surface)',
        border: `1px solid ${hovered ? 'var(--color-border)' : 'var(--color-border)'}`,
        borderRadius: 12,
        padding: 20,
        cursor: 'pointer',
        transition: 'transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease',
        transform: hovered ? 'translateY(-2px)' : 'none',
        boxShadow: hovered ? 'var(--color-shadow-md)' : 'none',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
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
              fontSize: 15,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
            }}
          >
            {vehicle.name}
          </div>
        </div>
        <StatusBadge status={status} size="lg" />
      </div>

      <DriverBadge vehicle={vehicle} />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 8,
        }}
      >
        <TelemetryItem
          icon={<Gauge size={13} />}
          label="Speed"
          value={`${Math.round(smoothSpeed)} km/h`}
        />
        <TelemetryItem
          icon={<Activity size={13} />}
          label="RPM"
          value={Math.round(smoothRpm).toLocaleString()}
        />
        <TelemetryItem
          icon={<Thermometer size={13} />}
          label="Coolant"
          value={vehicle.coolantTemp > 0 ? `${Math.round(smoothCoolant)}°C` : 'N/A'}
        />
      </div>

      {activeEvents.length > 0 && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 3,
          }}
        >
          {visibleEvents.map((evt) => (
            <div
              key={evt}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                padding: '4px 8px',
                borderRadius: 4,
                background: 'var(--color-red-bg)',
                border: '1px solid var(--color-red)',
                fontSize: 11,
                color: 'var(--color-red)',
                fontWeight: 500,
                lineHeight: 1.3,
              }}
            >
              <AlertTriangle size={10} style={{ flexShrink: 0 }} />
              {EVENT_LABELS[evt] || evt}
            </div>
          ))}
          {hiddenCount > 0 && (
            <button
              onClick={handleToggleEvents}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                padding: '3px 8px',
                borderRadius: 4,
                border: '1px dashed var(--color-border)',
                background: 'transparent',
                color: 'var(--color-text-muted)',
                fontSize: 11,
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
              <ChevronRight size={10} style={{ transform: eventsExpanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s ease' }} />
              +{hiddenCount} more
            </button>
          )}
        </div>
      )}

      <FuelBar level={vehicle.fuelLevel} />

      <VehicleHealthBar vehicle={vehicle} height={5} />

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: 4,
          borderTop: '1px solid var(--color-border-light)',
        }}
      >
        <span
          style={{
            fontSize: 11,
            color: 'var(--color-text-muted)',
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {relativeTime}
        </span>
        <button
          onClick={handleViewDetails}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            padding: '4px 8px',
            borderRadius: 6,
            border: 'none',
            background: 'transparent',
            color: 'var(--color-accent)',
            fontSize: 11,
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'background 0.15s ease',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-accent-subtle)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
        >
          <Eye size={12} />
          View Details
        </button>
      </div>
    </div>
  );
});

const DriverBadge = memo(function DriverBadge({ vehicle }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}
    >
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: 8,
          background: 'var(--color-accent-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-accent)',
          fontSize: 11,
          fontWeight: 600,
          flexShrink: 0,
        }}
      >
        {vehicle.driver.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
      </div>
      <div>
        <div
          style={{
            fontSize: 13,
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
});

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
          gap: 4,
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
