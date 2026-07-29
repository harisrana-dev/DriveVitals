import { useState } from 'react';
import { useVehicles } from '../../hooks/useFleetData';
import { useVehicleDrawer } from '../../context/VehicleDrawerContext';

const statusColors = {
  active: 'var(--color-green)',
  idle: 'var(--color-amber)',
  warning: 'var(--color-red)',
  offline: 'var(--color-text-muted)',
};

const statusBgs = {
  active: 'var(--color-green-bg)',
  idle: 'var(--color-amber-bg)',
  warning: 'var(--color-red-bg)',
  offline: 'var(--color-surface-hover)',
};

export function FleetPulse() {
  const vehicles = useVehicles();
  const { openDrawer } = useVehicleDrawer();
  const [hoveredId, setHoveredId] = useState(null);

  const active = vehicles.filter((v) => v.status === 'active').length;
  const idle = vehicles.filter((v) => v.status === 'idle').length;
  const warning = vehicles.filter((v) => v.status === 'warning').length;
  const offline = vehicles.filter((v) => v.status === 'offline').length;

  return (
    <div className="fade-in stagger-1" style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 12,
      padding: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 2 }}>
            Fleet Pulse
          </h3>
          <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            {vehicles.length} vehicles · Real-time status overview
          </p>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          {[
            { label: 'Active', count: active, color: statusColors.active },
            { label: 'Idle', count: idle, color: statusColors.idle },
            { label: 'Warning', count: warning, color: statusColors.warning },
            { label: 'Offline', count: offline, color: statusColors.offline },
          ].map((s) => (
            <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: 4, background: s.color }} />
              <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{s.label}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>{s.count}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(72px, 1fr))',
        gap: 8,
      }}>
        {vehicles.map((v) => (
          <div
            key={v.id}
            onClick={() => openDrawer(v)}
            onMouseEnter={() => setHoveredId(v.id)}
            onMouseLeave={() => setHoveredId(null)}
            style={{
              position: 'relative',
              padding: '10px 6px',
              borderRadius: 8,
              background: statusBgs[v.status],
              border: `1px solid ${hoveredId === v.id ? statusColors[v.status] : 'transparent'}`,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              textAlign: 'center',
              transform: hoveredId === v.id ? 'translateY(-2px)' : 'none',
            }}
          >
            <div style={{
              width: 10,
              height: 10,
              borderRadius: 5,
              background: statusColors[v.status],
              margin: '0 auto 6px',
              boxShadow: v.status === 'warning' ? `0 0 6px ${statusColors[v.status]}` : 'none',
            }} />
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 2 }}>
              {v.id}
            </div>
            <div style={{
              fontSize: 9,
              color: 'var(--color-text-muted)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}>
              {v.driver.split(' ')[0]}
            </div>

            {hoveredId === v.id && (
              <div style={{
                position: 'absolute',
                bottom: '100%',
                left: '50%',
                transform: 'translateX(-50%)',
                marginBottom: 6,
                background: 'var(--color-text-primary)',
                color: 'var(--color-surface)',
                padding: '6px 10px',
                borderRadius: 6,
                fontSize: 11,
                whiteSpace: 'nowrap',
                zIndex: 10,
                pointerEvents: 'none',
                boxShadow: 'var(--color-shadow-md)',
              }}>
                <div style={{ fontWeight: 600, marginBottom: 2 }}>{v.id} · {v.name}</div>
                <div>{v.driver}</div>
                <div style={{ marginTop: 2 }}>
                  Health: {v.healthScore}/100
                  {v.activeAlert && <span style={{ color: '#fcc419' }}> · {v.activeAlert}</span>}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
