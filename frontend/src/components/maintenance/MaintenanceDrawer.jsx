import { X } from 'lucide-react';
import { useMaintenanceVehicle } from '../../hooks/useMaintenance';
import { HealthStatusBadge } from '../vehicleHealth/HealthStatusBadge';
import { HealthBar } from '../vehicleHealth/HealthBar';
import { PriorityBadge } from './PriorityBadge';
import { DueBadge } from './DueBadge';
import { healthColor } from '../../utils/health';

const COMPONENT_STATUS = {
  overdue: { color: 'var(--color-red)', bg: 'var(--color-red-bg)', label: 'Overdue' },
  due: { color: 'var(--color-amber)', bg: 'var(--color-amber-bg)', label: 'Due' },
  ok: { color: 'var(--color-green)', bg: 'var(--color-green-bg)', label: 'OK' },
};

export function MaintenanceDrawer({ vehicleId, onClose }) {
  const result = useMaintenanceVehicle(vehicleId);
  if (!result) return null;

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
        <DrawerContent result={result} onClose={onClose} />
      </div>
    </>
  );
}

function DrawerContent({ result, onClose }) {
  const { vehicle, drawerData } = result;

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
        <VehicleInfo vehicle={vehicle} drawerData={drawerData} />
        <MaintenanceStatus drawerData={drawerData} />
        <RecommendedActions drawerData={drawerData} />
        <ServiceHistory drawerData={drawerData} />
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
          {(vehicle.vehicle_name || vehicle.vehicle_id).split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {vehicle.vehicle_name || vehicle.vehicle_id}
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
            {vehicle.vehicle_id} · {vehicle.driver_name || '\u2014'}
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

function VehicleInfo({ vehicle, drawerData }) {
  const color = healthColor(drawerData.health);
  return (
    <Section title="Vehicle Information">
      <div
        style={{
          padding: '16px 18px',
          borderRadius: 12,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
        }}
      >
        <div style={{ display: 'flex', gap: 16, marginBottom: 14 }}>
          <div style={{ position: 'relative', width: 72, height: 72, flexShrink: 0 }}>
            <svg width={72} height={72} viewBox="0 0 72 72">
              <circle cx={36} cy={36} r={30} fill="none" stroke="var(--color-border-light)" strokeWidth={5} />
              <circle
                cx={36} cy={36} r={30} fill="none" stroke={color} strokeWidth={5}
                strokeDasharray={`${(drawerData.health / 100) * 188.5} 188.5`}
                strokeLinecap="round"
                transform="rotate(-90 36 36)"
                style={{ transition: 'stroke-dasharray 0.4s ease' }}
              />
              <text x={36} y={36} textAnchor="middle" dy="5" fontSize="16" fontWeight="700" fill="var(--color-text-primary)">
                {Math.round(drawerData.health)}
              </text>
            </svg>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, justifyContent: 'center' }}>
            <HealthStatusBadge category={vehicle.overall_health_score >= 80 ? 'healthy' : vehicle.overall_health_score >= 50 ? 'warning' : 'critical'} />
            <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
              {vehicle.driver_name || '\u2014'}
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', fontSize: 12 }}>
          <DetailRow label="Odometer" value={`${drawerData.odometer.toLocaleString()} km`} />
          <DetailRow label="Fuel" value={`${Math.round(drawerData.fuelLevel)}%`} />
          <DetailRow label="Coolant" value={`${drawerData.coolantTemp.toFixed(1)} °C`} />
          <DetailRow label="Health" value={`${Math.round(drawerData.health)}%`} />
        </div>
      </div>
    </Section>
  );
}

function DetailRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <span style={{ color: 'var(--color-text-muted)' }}>{label}</span>
      <span style={{ color: 'var(--color-text-primary)', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    </div>
  );
}

function MaintenanceStatus({ drawerData }) {
  return (
    <Section title="Maintenance Status">
      <div
        style={{
          padding: '14px 16px',
          borderRadius: 8,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
        }}
      >
        {drawerData.outstanding.length === 0 && drawerData.upcomingServices.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>No outstanding services.</div>
        ) : (
          <>
            {drawerData.outstanding.length > 0 && (
              <div style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Outstanding
                </div>
                {drawerData.outstanding.map((svc) => (
                  <div key={svc.serviceType} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '4px 0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <DueBadge status={svc.dueStatus} />
                      <span style={{ fontSize: 12, color: 'var(--color-text-primary)', fontWeight: 500 }}>{svc.serviceType}</span>
                    </div>
                    <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                      {svc.remainingKm > 0 ? `${svc.remainingKm.toLocaleString()} km` : 'Overdue'}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {drawerData.upcomingServices.length > 0 && (
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Upcoming
                </div>
                {drawerData.upcomingServices.map((svc) => (
                  <div key={svc.type} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '4px 0' }}>
                    <span style={{ fontSize: 12, color: 'var(--color-text-primary)' }}>{svc.type}</span>
                    <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                      {svc.remainingKm > 0 ? `${svc.remainingKm.toLocaleString()} km` : 'Due'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </Section>
  );
}

function RecommendedActions({ drawerData }) {
  return (
    <Section title="Recommended Actions">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {drawerData.recommendations.map((rec) => {
          const st = COMPONENT_STATUS[rec.status] || COMPONENT_STATUS.ok;
          return (
            <div
              key={rec.component}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 12px',
                borderRadius: 8,
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border-light)',
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: st.color,
                  flexShrink: 0,
                }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                    {rec.component}
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 600,
                      padding: '1px 5px',
                      borderRadius: 3,
                      background: st.bg,
                      color: st.color,
                      letterSpacing: '0.03em',
                    }}
                  >
                    {st.label}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                  {rec.recommendation}
                </div>
              </div>
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>
                {rec.remainingKm > 0 ? `${rec.remainingKm.toLocaleString()} km` : 'Due'}
              </span>
            </div>
          );
        })}
      </div>
    </Section>
  );
}

function ServiceHistory({ drawerData }) {
  return (
    <Section title="Service History">
      <div
        style={{
          padding: '14px 16px',
          borderRadius: 8,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
        }}
      >
        {drawerData.history.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>No service history.</div>
        ) : (
          drawerData.history.map((h, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '6px 0',
                borderBottom: i < drawerData.history.length - 1 ? '1px solid var(--color-border-light)' : 'none',
              }}
            >
              <div
                style={{
                  width: 2,
                  height: 28,
                  borderRadius: 1,
                  background: 'var(--color-accent)',
                  flexShrink: 0,
                }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)' }}>
                  {h.serviceType}
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                  {h.date}
                </div>
              </div>
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                {h.mileage.toLocaleString()} km
              </span>
            </div>
          ))
        )}
      </div>
    </Section>
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
        style={{
          flex: 1,
          padding: '8px 12px',
          borderRadius: 8,
          border: 'none',
          background: 'var(--color-accent)',
          color: '#fff',
          fontSize: 13,
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'opacity 0.15s ease',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.85'; }}
        onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
      >
        Schedule Service
      </button>
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
        Export Record
      </button>
    </div>
  );
}
