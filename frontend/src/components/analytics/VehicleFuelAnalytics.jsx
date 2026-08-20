import { memo } from 'react';
import { Truck, HeartPulse } from 'lucide-react';
import { useVehicleDrawer } from '../../context/useVehicleDrawer';

function healthColor(status) {
  if (status === 'healthy') return 'var(--color-green)';
  if (status === 'warning') return 'var(--color-amber)';
  if (status === 'critical') return 'var(--color-red)';
  return 'var(--color-text-muted)';
}

export const VehicleFuelAnalytics = memo(function VehicleFuelAnalytics({ vehicleAnalytics }) {
  const vehicles = vehicleAnalytics?.vehicles || [];
  const { openDrawer } = useVehicleDrawer();

  return (
    <div>
      <h2 style={{
        fontSize: 14,
        fontWeight: 700,
        color: 'var(--color-text-primary)',
        marginBottom: 12,
        letterSpacing: '-0.01em',
      }}>
        Vehicle & Fuel Analytics
      </h2>

      <div style={{
        padding: '16px 20px',
        borderRadius: 14,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        overflow: 'auto',
      }}>
        {vehicles.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                {['Vehicle', 'Health', 'Trips', 'Distance', 'Fuel Eff.', 'Events', 'Events/100km'].map((h) => (
                  <th key={h} style={{
                    padding: '6px 8px',
                    textAlign: 'left',
                    fontSize: 10,
                    fontWeight: 600,
                    color: 'var(--color-text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {vehicles.map((v) => (
                <tr
                  key={v.vehicle_id}
                  onClick={() => openDrawer({ id: v.vehicle_id })}
                  style={{
                    borderBottom: '1px solid var(--color-border-light, var(--color-border))',
                    cursor: 'pointer',
                    transition: 'background 0.1s ease',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                >
                  <td style={{ padding: '10px 8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{
                        width: 28,
                        height: 28,
                        borderRadius: 7,
                        background: 'var(--color-blue-bg)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}>
                        <Truck size={13} style={{ color: 'var(--color-blue)' }} />
                      </div>
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>{v.vehicle_name}</div>
                        <div style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>{v.registration_number || v.vehicle_id}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '10px 8px' }}>
                    {v.health_score != null ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <HeartPulse size={12} style={{ color: healthColor(v.health_status) }} />
                        <span style={{ fontWeight: 600, color: healthColor(v.health_status) }}>
                          {v.health_score}
                        </span>
                      </div>
                    ) : (
                      <span style={{ color: 'var(--color-text-muted)' }}>—</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 8px', color: 'var(--color-text-secondary)' }}>
                    {v.completed_trips}
                  </td>
                  <td style={{ padding: '10px 8px', color: 'var(--color-text-secondary)' }}>
                    {v.total_distance_km != null ? `${v.total_distance_km} km` : '—'}
                  </td>
                  <td style={{ padding: '10px 8px', color: 'var(--color-text-secondary)', fontWeight: v.fuel_efficiency ? 600 : 400 }}>
                    {v.fuel_efficiency != null ? `${v.fuel_efficiency} km/L` : '—'}
                  </td>
                  <td style={{ padding: '10px 8px', color: 'var(--color-text-secondary)' }}>
                    {v.event_count}
                  </td>
                  <td style={{ padding: '10px 8px', color: 'var(--color-text-secondary)' }}>
                    {v.event_rate != null ? v.event_rate.toFixed(1) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: 120,
            color: 'var(--color-text-muted)',
            fontSize: 13,
          }}>
            No vehicle data available
          </div>
        )}
      </div>
    </div>
  );
});
