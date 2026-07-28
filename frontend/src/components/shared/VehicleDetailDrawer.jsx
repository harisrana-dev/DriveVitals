import { X, Thermometer, Fuel, Gauge, AlertTriangle, CheckCircle } from 'lucide-react';

function StatusBadge({ status }) {
  const colors = {
    active: { bg: 'var(--color-green-bg)', color: 'var(--color-green)', label: 'Active' },
    idle: { bg: 'var(--color-amber-bg)', color: 'var(--color-amber)', label: 'Idle' },
    warning: { bg: 'var(--color-red-bg)', color: 'var(--color-red)', label: 'Warning' },
    offline: { bg: 'var(--color-surface-hover)', color: 'var(--color-text-muted)', label: 'Offline' },
  };
  const c = colors[status] || colors.offline;
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 4,
      padding: '2px 8px',
      borderRadius: 4,
      background: c.bg,
      color: c.color,
      fontSize: 12,
      fontWeight: 500,
    }}>
      {status === 'active' && <span style={{ width: 6, height: 6, borderRadius: 3, background: c.color }} />}
      {status === 'warning' && <AlertTriangle size={11} />}
      {status === 'offline' && <span style={{ width: 6, height: 6, borderRadius: 3, background: c.color, opacity: 0.5 }} />}
      {c.label}
    </span>
  );
}

export function VehicleDetailDrawer({ vehicle, onClose }) {
  if (!vehicle) return null;

  const healthColor = vehicle.healthScore >= 85 ? 'var(--color-green)'
    : vehicle.healthScore >= 70 ? 'var(--color-amber)'
    : 'var(--color-red)';

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
      <div style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: 420,
        maxWidth: '90vw',
        height: '100vh',
        background: 'var(--color-surface)',
        borderLeft: '1px solid var(--color-border)',
        boxShadow: 'var(--color-shadow-lg)',
        zIndex: 301,
        display: 'flex',
        flexDirection: 'column',
        animation: 'slideInRight 0.2s ease-out',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid var(--color-border)',
        }}>
          <div>
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 2 }}>{vehicle.id}</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)' }}>{vehicle.name}</div>
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

        <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
            <StatusBadge status={vehicle.status} />
            <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
              Driver: {vehicle.driver}
            </span>
          </div>

          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Vehicle Health
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 48,
                height: 48,
                borderRadius: 10,
                background: `${healthColor}12`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 18,
                fontWeight: 700,
                color: healthColor,
              }}>
                {vehicle.healthScore}
              </div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-text-primary)', textTransform: 'capitalize' }}>
                  {vehicle.healthCategory}
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                  {vehicle.healthScore >= 85 ? 'Operating normally' : vehicle.healthScore >= 70 ? 'Needs monitoring' : 'Requires attention'}
                </div>
              </div>
            </div>
          </div>

          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Telemetry
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {[
                { icon: <Gauge size={16} />, label: 'Speed', value: `${vehicle.speed} km/h` },
                { icon: <Gauge size={16} />, label: 'RPM', value: vehicle.rpm.toLocaleString() },
                { icon: <Fuel size={16} />, label: 'Fuel', value: `${vehicle.fuelLevel}%` },
                { icon: <Thermometer size={16} />, label: 'Coolant', value: vehicle.coolantTemp > 0 ? `${vehicle.coolantTemp}\u00b0C` : 'N/A' },
              ].map((item) => (
                <div key={item.label} style={{
                  padding: '10px 12px',
                  borderRadius: 8,
                  background: 'var(--color-bg)',
                  border: '1px solid var(--color-border-light)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-text-muted)', marginBottom: 4 }}>
                    {item.icon}
                    <span style={{ fontSize: 11 }}>{item.label}</span>
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                    {item.value}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {vehicle.activeAlert && (
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Active Alert
              </div>
              <div style={{
                padding: '10px 12px',
                borderRadius: 8,
                background: 'var(--color-red-light)',
                border: '1px solid var(--color-red)',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}>
                <AlertTriangle size={15} style={{ color: 'var(--color-red)', flexShrink: 0 }} />
                <span style={{ fontSize: 13, color: 'var(--color-red)' }}>{vehicle.activeAlert}</span>
              </div>
            </div>
          )}

          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Details
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { label: 'Odometer', value: `${vehicle.odometer.toLocaleString()} km` },
                { label: 'Last Update', value: vehicle.lastUpdate },
                { label: 'Alerts', value: `${vehicle.alertCount} active` },
              ].map((item) => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--color-border-light)' }}>
                  <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{item.label}</span>
                  <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-primary)' }}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{
          padding: '12px 20px',
          borderTop: '1px solid var(--color-border)',
          display: 'flex',
          gap: 8,
        }}>
          <button style={{
            flex: 1,
            padding: '8px 12px',
            borderRadius: 8,
            background: 'var(--color-accent)',
            color: '#fff',
            fontSize: 13,
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-accent-hover)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-accent)'; }}
          >
            <CheckCircle size={14} />
            Acknowledge
          </button>
          <button style={{
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            color: 'var(--color-text-secondary)',
            fontSize: 13,
            fontWeight: 500,
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
      </div>
    </>
  );
}
