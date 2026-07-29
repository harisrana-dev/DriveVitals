import { useVehicles } from '../../hooks/useFleetData';
import { useVehicleDrawer } from '../../context/VehicleDrawerContext';
import { AlertTriangle, Fuel, Thermometer } from 'lucide-react';

const statusStyles = {
  active: { bg: 'var(--color-green-bg)', color: 'var(--color-green)', label: 'Active' },
  idle: { bg: 'var(--color-amber-bg)', color: 'var(--color-amber)', label: 'Idle' },
  warning: { bg: 'var(--color-red-bg)', color: 'var(--color-red)', label: 'Warning' },
  offline: { bg: 'var(--color-surface-hover)', color: 'var(--color-text-muted)', label: 'Offline' },
};

export function LiveFleetActivity() {
  const vehicles = useVehicles();
  const { openDrawer } = useVehicleDrawer();

  return (
    <div className="fade-in stagger-4" style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 12,
      overflow: 'hidden',
    }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border-light)' }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 2 }}>
          Live Fleet Activity
        </h3>
        <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
          Real-time telemetry from all vehicles
        </p>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border-light)' }}>
              {['Vehicle', 'Driver', 'Status', 'Speed', 'RPM', 'Fuel', 'Coolant', 'Health', 'Alert'].map((h) => (
                <th key={h} style={{
                  padding: '10px 16px',
                  textAlign: 'left',
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'var(--color-text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  whiteSpace: 'nowrap',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {vehicles.map((v) => {
              const st = statusStyles[v.status];
              return (
                <tr
                  key={v.id}
                  onClick={() => openDrawer(v)}
                  style={{
                    borderBottom: '1px solid var(--color-border-light)',
                    cursor: 'pointer',
                    transition: 'background 0.1s ease',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                >
                  <td style={{ padding: '10px 16px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: 13 }}>{v.id}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{v.name}</div>
                  </td>
                  <td style={{ padding: '10px 16px', color: 'var(--color-text-secondary)' }}>{v.driver}</td>
                  <td style={{ padding: '10px 16px' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                      padding: '2px 8px',
                      borderRadius: 4,
                      background: st.bg,
                      color: st.color,
                      fontSize: 12,
                      fontWeight: 500,
                    }}>
                      {v.status === 'active' && <span style={{ width: 5, height: 5, borderRadius: 3, background: st.color }} />}
                      {v.status === 'warning' && <AlertTriangle size={10} />}
                      {st.label}
                    </span>
                  </td>
                  <td style={{ padding: '10px 16px', fontWeight: 500, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
                    {v.speed > 0 ? `${v.speed} km/h` : '\u2014'}
                  </td>
                  <td style={{ padding: '10px 16px', color: 'var(--color-text-secondary)', fontVariantNumeric: 'tabular-nums' }}>
                    {v.rpm > 0 ? v.rpm.toLocaleString() : '\u2014'}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Fuel size={13} style={{ color: v.fuelLevel < 30 ? 'var(--color-amber)' : 'var(--color-text-muted)' }} />
                      <span style={{
                        fontWeight: 500,
                        color: v.fuelLevel < 30 ? 'var(--color-amber)' : 'var(--color-text-primary)',
                      }}>
                        {v.fuelLevel}%
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Thermometer size={13} style={{ color: v.coolantTemp > 100 ? 'var(--color-red)' : 'var(--color-text-muted)' }} />
                      <span style={{
                        fontWeight: 500,
                        color: v.coolantTemp > 100 ? 'var(--color-red)' : 'var(--color-text-primary)',
                      }}>
                        {v.coolantTemp > 0 ? `${v.coolantTemp}\u00b0C` : '\u2014'}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{
                        width: 32,
                        height: 4,
                        borderRadius: 2,
                        background: 'var(--color-border)',
                        overflow: 'hidden',
                      }}>
                        <div style={{
                          width: `${v.healthScore}%`,
                          height: '100%',
                          borderRadius: 2,
                          background: v.healthScore >= 85 ? 'var(--color-green)' : v.healthScore >= 70 ? 'var(--color-amber)' : 'var(--color-red)',
                        }} />
                      </div>
                      <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
                        {v.healthScore}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    {v.activeAlert ? (
                      <span style={{
                        fontSize: 11,
                        color: 'var(--color-amber)',
                        fontWeight: 500,
                      }}>
                        {v.activeAlert}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>\u2014</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
