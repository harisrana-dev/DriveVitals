import { X } from 'lucide-react';
import { useVehicle } from '../../hooks/useVehicleHealth';
import { useRelativeTime } from '../../hooks/useRelativeTime';
import { HealthStatusBadge } from './HealthStatusBadge';
import { HealthBar } from './HealthBar';
import { healthCategory, healthColor, componentLabel } from '../../utils/health';

const COMPONENT_KEYS = ['engine', 'braking', 'fuel', 'behaviour'];

const EVENT_LABELS = {
  harsh_braking: 'Harsh Braking',
  aggressive_throttle: 'Aggressive Throttle',
  high_rpm: 'High RPM',
  speeding: 'Speeding',
};

export function VehicleHealthDrawer({ vehicleId, onClose }) {
  const vehicle = useVehicle(vehicleId);
  if (!vehicle) return null;

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
        <DrawerContent vehicle={vehicle} onClose={onClose} />
      </div>
    </>
  );
}

function DrawerContent({ vehicle, onClose }) {
  const relativeTime = useRelativeTime(vehicle.lastUpdated);

  const activeIssues = vehicle.activeEvents.map((evt) => ({
    label: EVENT_LABELS[evt] || evt,
    active: true,
  }));

  if (activeIssues.length === 0) {
    activeIssues.push({ label: 'No active issues', active: false });
  }

  return (
    <>
      <Header vehicle={vehicle} onClose={onClose} />

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
        <HealthOverview vehicle={vehicle} relativeTime={relativeTime} />

        <Section title="Component Health">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {COMPONENT_KEYS.map((key) => (
              <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                  <span style={{ color: 'var(--color-text-secondary)', fontWeight: 500 }}>{componentLabel(key)}</span>
                  <span style={{ color: 'var(--color-text-primary)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                    {Math.round(vehicle.components[key])}%
                  </span>
                </div>
                <HealthBar score={vehicle.components[key]} height={6} />
              </div>
            ))}
          </div>
        </Section>

        <Section title="Active Events">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {activeIssues.map((issue, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 12px',
                  borderRadius: 8,
                  background: issue.active ? 'var(--color-red-bg)' : 'var(--color-bg)',
                  border: `1px solid ${issue.active ? 'var(--color-red)' : 'var(--color-border-light)'}`,
                  fontSize: 13,
                  fontWeight: issue.active ? 500 : 400,
                  color: issue.active ? 'var(--color-red)' : 'var(--color-text-muted)',
                }}
              >
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: issue.active ? 'var(--color-red)' : 'var(--color-text-muted)',
                    flexShrink: 0,
                  }}
                />
                {issue.label}
              </div>
            ))}
          </div>
        </Section>

        <Section title="Recent Condition">
          <div
            style={{
              padding: '12px 14px',
              borderRadius: 8,
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border-light)',
              fontSize: 12,
              color: 'var(--color-text-secondary)',
              lineHeight: 1.6,
            }}
          >
            <div>Speed: {vehicle.speed.toFixed(1)} km/h</div>
            <div>RPM: {Math.round(vehicle.rpm)}</div>
            <div>Coolant: {vehicle.coolantTemp.toFixed(1)} °C</div>
            <div>Engine Load: {vehicle.engineLoad.toFixed(1)}%</div>
            <div>Fuel Level: {vehicle.fuelLevel.toFixed(1)}%</div>
            <div>Last updated: {relativeTime}</div>
          </div>
        </Section>

        <Section title="Maintenance">
          <div
            style={{
              padding: '12px 14px',
              borderRadius: 8,
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border-light)',
              fontSize: 12,
              color: 'var(--color-text-muted)',
              fontStyle: 'italic',
            }}
          >
            Maintenance scheduling and service history will appear here when integrated with the maintenance module.
          </div>
        </Section>
      </div>

      <Footer onClose={onClose} />
    </>
  );
}

function Header({ vehicle, onClose }) {
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
          {vehicle.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {vehicle.name}
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
            {vehicle.id} · {vehicle.driverName}
          </div>
        </div>
      </div>
      <button
        onClick={onClose}
        aria-label="Close"
        style={{
          width: 32, height: 32, borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--color-text-muted)', background: 'transparent',
          border: 'none', cursor: 'pointer',
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

function HealthOverview({ vehicle, relativeTime }) {
  const cat = healthCategory(vehicle.overallHealth);
  const color = healthColor(cat);

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
      <div style={{ position: 'relative', width: 88, height: 88, flexShrink: 0 }}>
        <svg width={88} height={88} viewBox="0 0 88 88">
          <circle cx={44} cy={44} r={37} fill="none" stroke="var(--color-border-light)" strokeWidth={6} />
          <circle
            cx={44} cy={44} r={37} fill="none" stroke={color} strokeWidth={6}
            strokeDasharray={`${(vehicle.overallHealth / 100) * 232.5} 232.5`}
            strokeLinecap="round"
            transform="rotate(-90 44 44)"
            style={{ transition: 'stroke-dasharray 0.4s ease' }}
          />
          <text x={44} y={44} textAnchor="middle" dy="5" fontSize="20" fontWeight="700" fill="var(--color-text-primary)">
            {Math.round(vehicle.overallHealth)}
          </text>
        </svg>
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6, justifyContent: 'center' }}>
        <HealthStatusBadge category={vehicle.healthCategory} />
        <div style={{ fontSize: 13, color: 'var(--color-text-primary)', fontWeight: 500 }}>
          {vehicle.driverName}
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
          Updated {relativeTime}
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div>
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
        {title}
      </div>
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
